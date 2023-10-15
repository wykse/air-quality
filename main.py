from pathlib import Path

from air_quality.classes import Service
from air_quality.utils import csv_to_points


def main():
    # Url to image service
    url = "https://mapservices.weather.noaa.gov/raster/rest/services/air_quality/ndgd_apm25_hr01_bc/ImageServer"

    # Path to the csv file
    path = Path(__file__).parent / "data" / "points.csv"

    # Instantiate a service object to manage getting service information
    service = Service(url=url)

    # Get a list of points from csv
    points = csv_to_points(path=path)

    # List to store identify results
    results = []

    # Get pixel values from image service for each point
    for point in points[3:4]:
        result = service.identify(point)
        results.append(result)
        print(result)


if __name__ == "__main__":
    main()
