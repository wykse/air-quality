from pathlib import Path

import pandas as pd
import plotly.express as px

from air_quality.utils import plot_line

path = "output/output_example.csv"

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
fig.show()

print(df)

# Write figure to html
output_directory = Path(path).parent
path_to_plot = output_directory / f"{Path(path).stem}-plot.html"
fig.write_html(path_to_plot)

print(f"Plot saved to {path_to_plot}")


# plot_line("output/output_example.csv")
