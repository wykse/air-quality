import csv
import re
from pathlib import Path

import pandas as pd
import plotly.express as px


def read_csv_dict(path: str) -> list[dict]:
    # Initialize an empty list to store the dictionaries
    data_list = []

    # Read the csv file and parse it into dictionaries
    with open(path, "r") as csvfile:
        # Create a DictReader
        reader = csv.DictReader(csvfile)

        # Iterate over each row (each row is a dictionary)
        for row in reader:
            # Append the row dictionary to the list
            data_list.append(row)

    return data_list


def write_dict_csv(data: list[dict], path: str):
    # Get field names from the dict keys
    fieldnames = data[0].keys()

    with open(path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        # Write header
        writer.writeheader()

        # Write data
        for row in data:
            writer.writerow(row)

    print(f"Data written to {path}")


def combine_csv_files(directory: str, output: str, filenames: list[str] = None):
    # List to store combined data
    combined_data = []

    directory_path = Path(directory)

    # List CSV files in the directory
    csv_files = [
        f for f in directory_path.iterdir() if f.is_file() and f.suffix == ".csv"
    ]

    # Filter by specified filenames if provided
    if filenames:
        csv_files = [f for f in csv_files if f.name in filenames]

    # Iterate through CSV files and combine them
    for csv_file in csv_files:
        with open(csv_file, "r", newline="") as file:
            csv_reader = csv.reader(file)
            # Skip header for all files except the first one
            if combined_data:
                next(csv_reader)
            for row in csv_reader:
                combined_data.append(row)

    # Write combined data to output csv file
    with open(output, "w", newline="") as file:
        csv_writer = csv.writer(file)
        for row in combined_data:
            csv_writer.writerow(row)

    print(f"Combined data saved to {output}")


def flatten_dict(nested_dict: dict, parent_key: str = "", separator: str = "_") -> dict:
    """Flatten a nested dictionary.

    Args:
        nested_dict (dict): The nested dictionary to flatten.
        parent_key (str, optional): The concatenated key of the parent dictionary (used for recursion). Defaults to "".
        separator (str, optional): The separator to use for joining keys. Defaults to "_".

    Returns:
        dict: Flattened dictionary.
    """

    flattened_dict = {}
    for key, value in nested_dict.items():
        new_key = parent_key + separator + key if parent_key else key
        if isinstance(value, dict):
            flattened_dict.update(flatten_dict(value, new_key, separator))
        else:
            flattened_dict[new_key] = value
    return flattened_dict


def plot_line(path: str):
    # Read csv into df
    df = pd.read_csv(path)

    # Sort values
    df = df.sort_values(by=["location_name", "idp_issueddate", "idp_validtime"])

    # Image server sometimes contain 217 rasters instead of the expected 144
    # Filter out the nulls
    df = df.loc[df["idp_issueddate"].notna()]

    # Filter for latest issued date
    latest_issued_on = max(df["idp_issueddate"].values)
    df = df.loc[df["idp_issueddate"] == latest_issued_on]

    # Add new col with name and coordinates
    df["location"] = (
        df["location_name"]
        + " ("
        + df["location_coordinates_y"].astype(str)
        + ", "
        + df["location_coordinates_x"].astype(str)
        + ")"
    )

    # Plot line chart
    title = df["attributes_idp_grb_elem"].unique()[0].strip()

    fig = px.line(df, x="idp_validtime", y="value", color="location", title=title)

    # Show figure
    # fig.show()

    # Write figure to html
    output_directory = Path(path).parent
    path_to_plot = output_directory / f"{Path(path).stem}-plot.html"
    fig.write_html(path_to_plot)

    print(f"Plot saved to {path_to_plot}")

    return fig


def clean_and_covert(input_str: str) -> str:
    """
    Converts input str to lowercase, replaces special chars, and
    replaces spaces with underscores, and trims the str.

    Args:
        input_str (str): Input str.

    Returns:
        str: Cleaned str.
    """
    input_str_trimmed = input_str.strip()

    input_str_lower = input_str_trimmed.lower()

    # Replace special characters with underscores
    input_str_no_special = re.sub(r"[^a-zA-Z0-9]", "_", input_str_lower)

    # Replace spaces with underscores
    input_str_final = input_str_no_special.replace(" ", "_")

    return input_str_final
