import csv

from air_quality.classes import Coordinates, Point


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
