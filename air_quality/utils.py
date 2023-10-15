import csv
import json

import requests
from classes import Coordinates, Point


def csv_to_points(path: str) -> list[Point]:
    # List to store the data from the CSV file
    points = []

    # Open the CSV file and read its content
    with open(path, "r") as csvfile:
        csv_reader = csv.reader(csvfile)

        # SKip the header row
        next(csv_reader)

        # Read and append the remaining rows
        for row in csv_reader:
            c = Coordinates(x=row[2], y=row[1])
            points.append(Point(name=row[0], coordinates=c))

    return points


def project_coordinates(points: list[Coordinates], url: str) -> dict:
    """Project coordinates using the service's project endpoint.

    E.g.: https://mapservices.weather.noaa.gov/raster/rest/services/air_quality/ndgd_apm25_hr01_bc/ImageServer/project
    Reference: https://mapservices.weather.noaa.gov/raster/sdk/rest/index.html#/Project_Image_Service/02ss000000pv000000/

    Args:
        points (list[Coordinates]): A list of Coordinates.
        url (str): Url for the project API endpoint.

    Returns:
        dict: Projected geometry in the same order as provided.
    """
    geometries = [{"x": point.x, "y": point.y} for point in points]

    geo_param = {"geometrytype": "esriGeometryPoint", "geometries": geometries}

    # Get the spatial reference from the first point
    in_sr = points[0].wkid

    # Get spatial reference of image service
    # Remove "project" from the end of the URL
    service_url = url.rsplit("/", 1)[0]

    # Append json format query param to service url
    service_url = service_url + "?f=json"

    service_r = requests.get(service_url)

    out_sr = service_r.json()["spatialReference"]["latestWkid"]

    payload = {
        "geometries": json.dumps(geo_param),
        "inSR": in_sr,
        "outSR": out_sr,
        "f": "json",
    }

    # Send a GET request
    response = requests.get(url, params=payload)

    # Check if the request was successful (HTTP status code 200)
    if response.status_code == 200:
        return response.json()
    else:
        # Print an error message if the request was not successful
        print("Error:", response.status_code)
