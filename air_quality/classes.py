import json
from datetime import datetime, timezone

import requests
from attrs import asdict, define, field
from dateutil import tz

from .utils import flatten_dict, write_dict_csv

# Time zone identifier from tz database
# https://en.wikipedia.org/wiki/List_of_tz_database_time_zones
TIMEZONE = "America/Los_Angeles"


@define
class Coordinates:
    x: float
    y: float
    wkid: int = 4326

    @classmethod
    def from_dict(
        cls,
        data: dict,
        x_fieldname: str = "long",
        y_fieldname: str = "lat",
        wkid: int = 4326,
    ):
        return cls(x=data.get(x_fieldname), y=data.get(y_fieldname), wkid=wkid)

    def to_json_str_geometry(self) -> str:
        """Serialize long and lat into a json formatted string for ArcGIS REST API.
        Reference: https://mapservices.weather.noaa.gov/raster/sdk/rest/02ss/02ss0000008m000000.htm#POINT
        """
        g = {"x": self.x, "y": self.y, "spatialReference": {"wkid": self.wkid}}
        return json.dumps(g)


@define
class Point:
    name: str
    coordinates: Coordinates

    @classmethod
    def from_dict(
        cls,
        data: dict,
        name_fieldname: str = "name",
        x_fieldname: str = "long",
        y_fieldname: str = "lat",
        wkid: int = 4326,
    ):
        return cls(
            name=data.get(name_fieldname),
            coordinates=Coordinates.from_dict(
                data=data, x_fieldname=x_fieldname, y_fieldname=y_fieldname, wkid=wkid
            ),
        )


@define(order=True)
class Raster:
    idp_issueddate: datetime = field(init=False, default=None)
    idp_validtime: datetime = field(init=False, default=None)
    value: str
    location: Point
    attributes: dict

    def __attrs_post_init__(self):
        if self.attributes["idp_validtime"] is not None:
            timestamp = self.attributes["idp_validtime"] / 1000
            self.idp_validtime = datetime.fromtimestamp(
                timestamp, timezone.utc
            )  # Time is in milliseconds, convert to seconds
        if self.attributes["idp_issueddate"] is not None:
            timestamp = self.attributes["idp_issueddate"] / 1000
            self.idp_issueddate = datetime.fromtimestamp(
                timestamp, timezone.utc
            )  # Time is in milliseconds, convert to seconds

    def as_dict(self) -> dict:
        return asdict(self)

    def as_flat_dict(self) -> dict:
        return flatten_dict(self.as_dict())


@define
class IdentifyResult:
    service_name: str
    rasters: list[Raster]
    content: dict
    url: str
    requested_on: datetime

    def to_csv(self, path: str):
        flattened_rasters = []
        for r in self.rasters:
            # Add additional info to row for csv
            row = r.as_flat_dict()
            row["service_name"] = self.service_name
            row["url"] = self.url
            row["requested_on"] = self.requested_on
            flattened_rasters.append(row)

        write_dict_csv(flattened_rasters, path)


@define
class Service:
    url: str
    name: str = field(init=False)
    start_time: datetime = field(init=False)
    end_time: datetime = field(init=False)
    spatial_reference: dict = field(init=False)
    content: dict = field(init=False)

    def __attrs_post_init__(self):
        # Add f=json query param to url
        r = requests.get(self.url, params={"f": "json"})
        data = r.json()

        self.name = data["name"]

        # Time stamp is Epoch time in milliseconds
        self.start_time = datetime.fromtimestamp(
            data["timeInfo"]["timeExtent"][0] / 1000, timezone.utc
        )
        self.end_time = datetime.fromtimestamp(
            data["timeInfo"]["timeExtent"][1] / 1000, timezone.utc
        )

        self.spatial_reference = data["spatialReference"]

        self.content = data

        return

    def identify(self, point: Point) -> IdentifyResult | dict:
        """Get all pixel values from image service at Point.

        E.g., image service: https://mapservices.weather.noaa.gov/raster/rest/services/air_quality/ndgd_apm25_hr01_bc/ImageServer/identify
        Reference: https://mapservices.weather.noaa.gov/raster/sdk/rest/index.html#/Project_Image_Service/02ss000000pv000000/

        Args:
            point (Point): Point location for pixel values.

        Returns:
            IdentifyResult: Pixel values for point location.
        """

        # Construct url to API identify endpoint
        if self.url.split("/")[-1] == "":
            url = self.url + "identify"
        else:
            url = self.url + "/identify"

        payload = {
            "geometry": point.coordinates.to_json_str_geometry(),
            "geometryType": "esriGeometryPoint",
            "returnGeometry": False,
            "returnCatalogItems": True,
            "returnPixelValues": True,
            "processAsMultidimensional": False,
            "f": "json",
        }

        requested_on = datetime.now(tz=tz.gettz(TIMEZONE))

        r = requests.get(url, params=payload)

        data = r.json()

        # Check if error
        error = data.get("error")
        if error is not None:
            return error

        # Zip values and rasters
        values_temp = data["properties"]["Values"]
        rasters_temp = data["catalogItems"]["features"]

        # print(f"count values: {len(values_temp)}, count rasters: {len(rasters_temp)}")

        # TODO: log
        if len(values_temp) == len(rasters_temp):
            zipped_values_rasters = list(zip(values_temp, rasters_temp))

        # List to store the rasters
        rasters_list = []

        for v, ras in zipped_values_rasters:
            # Get rasters and append to list
            raster = Raster(value=v, attributes=ras["attributes"], location=point)
            rasters_list.append(raster)

        return IdentifyResult(
            service_name=self.name,
            rasters=rasters_list,
            content=data,
            url=r.url,
            requested_on=requested_on,
        )

    def project(self, points: list[Point], in_sr: int = 4326) -> dict:
        # Construct url to API project endpoint
        if self.url.split("/")[-1] == "":
            url = self.url + "project"
        else:
            url = self.url + "/project"

        geometries = [
            {"x": point.coordinates.x, "y": point.coordinates.y} for point in points
        ]

        geo_param = {"geometrytype": "esriGeometryPoint", "geometries": geometries}

        payload = {
            "geometries": json.dumps(geo_param),
            "inSR": in_sr,
            "outSR": self.spatial_reference["latestWkid"],
            "f": "json",
        }

        # Send a GET request
        r = requests.get(url, params=payload)

        data = r.json()

        # Check if error
        error = data.get("error")
        if error is not None:
            return error
        else:
            return data
