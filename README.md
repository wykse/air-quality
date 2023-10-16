# air_quality
Get air quality data from National Weather Service's ArcGIS REST image service, e.g., [air_quality/ndgd_apm25_hr01_bc](https://mapservices.weather.noaa.gov/raster/rest/services/air_quality/ndgd_apm25_hr01_bc/ImageServer).

Read more about [NWS Air Quality Forecast Guidance](https://vlab.noaa.gov/web/osti-modeling/air-quality).

## Installation
Clone repo, create virtual environment, then install packages.
```
pip install -r requirements.txt
```

## Usage
```
usage: main.py [-h] [-p | --plot | --no-plot] url input output

Get NOAA's Air Quality Forecast Guidance as a csv

positional arguments:
  url                   url for ArcGIS image service, e.g., https://mapservices.weather.noaa.gov/raster/rest/services/air_quality/ndgd_apm25_hr01_bc/ImageServer
  input                 path to csv containing input points; header must have following field names: name, lat, long
  output                path to output csv

options:
  -h, --help            show this help message and exit
  -p, --plot, --no-plot
                        plot output as a line chart
```

### Example with plot
```
python .\main.py https://mapservices.weather.noaa.gov/raster/rest/services/air_quality/ndgd_apm25_hr01_bc/ImageServer data/input_example.csv data/output_example.csv --plot
```

```
Requesting values from air_quality/ndgd_apm25_hr01_bc for 3 points...
100%|████████████████████████████████████████████| 3/3 [00:16<00:00,  5.45s/it]
Data written to data/output_example.csv
Plotted output_example.csv
```

![Plot example](/assets/images/plot.png)

## TODO
- Add logging
- Add async