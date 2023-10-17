import argparse
import time
from pathlib import Path

from tqdm import tqdm

from air_quality.classes import Point, Service
from air_quality.utils import (
    clean_and_covert,
    combine_csv_files,
    plot_line,
    read_csv_dict,
)

SCRATCH_DIR = Path("./scratch")


def main(args):
    # Url to image service
    url = args.url

    # Path to the csv file
    csv_path = args.input

    # Read csv file and store each row as a dict in a list
    data_list = read_csv_dict(csv_path)

    # Create points from the list of dictionaries
    points = [Point.from_dict(item) for item in data_list]

    # Create scratch csv filenames for each point
    scratch_filenames = []
    i = 0
    filenames_and_points = []
    for p in points:
        # Clean point name for use as filename for sratch files
        clean_name = clean_and_covert(p.name)

        # Filename for scratch file
        scratch_filename = f"{i}-{clean_name}-output.csv"
        scratch_filenames.append(scratch_filename)

        i += 1

    filenames_and_points = list(zip(scratch_filenames, points))

    # Instantiate a service object to manage getting service information
    service = Service(url=url)

    # Sractch csv files that already exist
    current_scratch_files = [
        f.name for f in SCRATCH_DIR.iterdir() if f.is_file() and f.suffix == ".csv"
    ]

    # Get pixel values from image service for each point
    print(f"Requesting values from {service.name} for {len(points)} points...")
    for scratch_filename, point in tqdm(filenames_and_points):
        # Skip point if scratch csv file exists
        if scratch_filename in current_scratch_files:
            print(
                f"Skipping {point.name} ({point.coordinates.x}, {point.coordinates.y}) because {scratch_filename} in {SCRATCH_DIR}"
            )
            continue

        # Get values from image service
        print(
            f"Requesting values for {point.name} ({point.coordinates.x}, {point.coordinates.y})"
        )
        result = service.identify(point)

        # Write to a csv in scratch dir
        result.to_csv(SCRATCH_DIR / scratch_filename)

        # Delay for 5 seconds
        time.sleep(5)

    # Get all the scratch csvs and combine them
    combine_csv_files(
        directory=SCRATCH_DIR, output=args.output, filenames=scratch_filenames
    )

    # Plot output as line chart
    if args.plot:
        fig = plot_line(args.output)

    # Clean up scratch
    print(f"Cleaning up {SCRATCH_DIR}...")
    for filename in scratch_filenames:
        path_to_file = SCRATCH_DIR / filename
        try:
            Path(path_to_file).unlink()
            print(f"File '{path_to_file}' successfully deleted.")
        except FileNotFoundError:
            print(f"File '{path_to_file}' not found.")
        except PermissionError:
            print(f"Permission denied to delete file '{path_to_file}'.")


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
