import json
from datetime import datetime, timezone

import requests
from attrs import asdict, define, field

from .utils import flatten_dict


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
            self.idp_validtime = datetime.fromtimestamp(
                self.attributes["idp_validtime"] / 1000
            )  # Time is in milliseconds, convert to seconds
        if self.attributes["idp_issueddate"] is not None:
            self.idp_issueddate = datetime.fromtimestamp(
                self.attributes["idp_issueddate"] / 1000
            )  # Time is in milliseconds, convert to seconds

    def as_dict(self):
        return asdict(self)

    def as_flat_dict(self):
        return flatten_dict(self.as_dict())


@define
class IdentifyResult:
    service_name: str
    rasters: list[Raster]
    content: dict
    url: str


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

    def identify(self, point: Point) -> IdentifyResult:
        # Get pixel values
        # API: https://mapservices.weather.noaa.gov/raster/rest/services/air_quality/ndgd_apm25_hr01_bc/ImageServer/identify
        # Reference: https://mapservices.weather.noaa.gov/raster/sdk/rest/index.html#/Project_Image_Service/02ss000000pv000000/

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

        if len(values_temp) == len(rasters_temp):
            zipped_values_rasters = list(zip(values_temp, rasters_temp))

        # List to store the rasters
        rasters_list = []

        # Count values to see progress
        i = 0
        for v, ras in zipped_values_rasters:
            # Get rasters and append to list
            raster = Raster(value=v, attributes=ras["attributes"], location=point)

            rasters_list.append(raster)

            # print(f"{i} - value: {v}, time_series: {ras["attributes"]["idp_time_series"]}")

            i += 1

        return IdentifyResult(
            service_name=self.name, rasters=rasters_list, content=data, url=r.url
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
