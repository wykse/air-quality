import json
from datetime import datetime

import requests
from attrs import define, field


@define
class ServiceInfo:
    name: str
    url: str


@define(order=True)
class Raster:
    idp_issueddate: datetime = field(init=False)
    idp_validtime: datetime = field(init=False)
    value: str
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


@define
class ServiceResult:
    rasters: list[Raster]
    content: dict


@define
class Coordinates:
    x: float
    y: float
    wkid: int = 4326

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
    result: ServiceResult = field(init=False)

    def identify(self, url: str):
        # Get pixel values
        # API: https://mapservices.weather.noaa.gov/raster/rest/services/air_quality/ndgd_apm25_hr01_bc/ImageServer/identify
        # Reference: https://mapservices.weather.noaa.gov/raster/sdk/rest/index.html#/Project_Image_Service/02ss000000pv000000/

        payload ={"geometry": self.coordinates.to_json_str_geometry(),
                "geometryType": "esriGeometryPoint",
                "returnGeometry": False,
                "returnCatalogItems": True,
                "returnPixelValues": True,
                "processAsMultidimensional": False,
                "f": "json"}

        r = requests.get(url, params=payload)

        data = r.json()

        # Zip values and rasters
        values_temp = data["properties"]["Values"]
        rasters_temp = data["catalogItems"]["features"]

        print(f"count values: {len(values_temp)}, count rasters: {len(rasters_temp)}")

        if len(values_temp) == len(rasters_temp):
            zipped_values_rasters = list(zip(values_temp, rasters_temp))

        # List to store the rasters
        rasters_list = []

        # Count values to see progress
        i = 0
        for v, r in zipped_values_rasters:
            # Get rasters and append to list
            raster = Raster(
                value=v,
                attributes=r["attributes"],
            )

            rasters_list.append(raster)

            print(f"{i} - value: {v}, time_series: {r["attributes"]["idp_time_series"]}")

            i += 1

        # Sort rasters
        rasters_list = sorted(rasters_list)

        # Add identify result to point
        self.result = ServiceResult(rasters=rasters_list, content=data)

        return
