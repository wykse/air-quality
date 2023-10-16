import csv


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
