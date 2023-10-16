import argparse

from tqdm import tqdm

from air_quality.classes import Point, Service
from air_quality.utils import plot_line, read_csv_dict, write_dict_csv


def main(args):
    # Url to image service
    url = args.url

    # Path to the csv file
    csv_path = args.input

    # Read csv file and store each row as a dict in a list
    data_list = read_csv_dict(csv_path)

    # Create points from the list of dictionaries
    points = []
    for item in data_list:
        p = Point.from_dict(item)
        points.append(p)

    # Instantiate a service object to manage getting service information
    service = Service(url=url)

    # List to store identify results
    results = []

    # Get pixel values from image service for each point
    print(f"Requesting values from {service.name} for {len(points)} points...")
    for point in tqdm(points):
        result = service.identify(point)
        results.append(result)

    # Get all the results into a list then write to csv
    all_points_results = []

    # Go through each point's result's rasters and append to list
    for result in results:
        for raster in result.rasters:
            r = raster.as_flat_dict()
            all_points_results.append(r)

    # Write to csv
    write_dict_csv(all_points_results, args.output)

    # Plot output as line chart
    if args.plot:
        fig = plot_line(args.output)


if __name__ == "__main__":
    # Set up parser for command line
    parser = argparse.ArgumentParser(
        description="Get NOAA's Air Quality Forecast Guidance as a csv"
    )
    parser.add_argument(
        "url",
        help="url for ArcGIS image service, e.g., https://mapservices.weather.noaa.gov/raster/rest/services/air_quality/ndgd_apm25_hr01_bc/ImageServer",
    )
    parser.add_argument(
        "input",
        help="path to csv containing input points; header must have following field names: name, lat, long",
    )
    parser.add_argument("output", help="path to output csv")
    parser.add_argument(
        "-p",
        "--plot",
        action=argparse.BooleanOptionalAction,
        help="plot output as a line chart",
    )
    args = parser.parse_args()

    main(args)
