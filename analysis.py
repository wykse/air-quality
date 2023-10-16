import pandas as pd
import plotly.express as px

# Read csv into df
df = pd.read_csv("./data/output.csv")

# Sort values
df = df.sort_values(by=["location_name", "idp_issueddate", "idp_validtime"])

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
fig.show()
