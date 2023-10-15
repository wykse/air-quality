from pathlib import Path

from utils import csv_to_points


def main():
    # Url to image service
    url = "https://mapservices.weather.noaa.gov/raster/rest/services/air_quality/ndgd_apm25_hr01_bc/ImageServer/identify"
    # Path to the csv file
    path = Path(__file__).parents[1] / "data" / "points.csv"

    # Get a list of points from csv
    points = csv_to_points(path=path)

    # Get pixel values from image service for each point
    for point in points[3:4]:
        point.identify(url=url)
        print(point)


if __name__ == "__main__":
    main()
