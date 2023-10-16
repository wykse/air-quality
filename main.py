from tqdm import tqdm

from air_quality.classes import Point, Service
from air_quality.utils import read_csv_dict, write_dict_csv


def main():
    # Url to image service
    url = "https://mapservices.weather.noaa.gov/raster/rest/services/air_quality/ndgd_apm25_hr01_bc/ImageServer"

    # Path to the csv file
    csv_path = "./data/input.csv"

    # Read csv file and store each row as a dict in a list
    data_list = read_csv_dict(csv_path)

    # Create points from the list of dictionaries
    points = []
    for item in data_list:
        p = Point.from_dict(
            item, name_fieldname="name", x_fieldname="long", y_fieldname="lat"
        )
        points.append(p)

    # Instantiate a service object to manage getting service information
    service = Service(url=url)

    # List to store identify results
    results = []

    # Get pixel values from image service for each point
    print("Requesting pixel values for points...")
    for point in tqdm(points[4:6]):
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
    write_dict_csv(all_points_results, "./data/output.csv")


if __name__ == "__main__":
    main()
