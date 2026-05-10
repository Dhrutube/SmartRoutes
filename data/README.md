# Data Setup

The raw data files are too large for git. Download them locally before running any notebooks.

## Files needed

### 1. CityIQ Pedestrian Data (~1 GB)
- Source: https://data.smartcitiessd.com/dataset/pedestrian-counts
- Download `pedestrians.csv` and `segments.csv`
- Place in: `data/cityiq.io-pedestrians-san_diego-1/data/pedestrians.csv` and `data/cityiq.io-pedestrians-san_diego-1/notebooks/segments.csv`

### 2. MTS GTFS Static
- Source: https://www.sdmts.com/schedules/google-transit
- Download `google_transit.zip`, extract all `.txt` files
- Place at: `data/` (top level — `stops.txt`, `routes.txt`, `trips.txt`, `stop_times.txt`, etc.)

### 3. San Diego Census 2017
- Source: https://www.kaggle.com/datasets/ifeanyichukwunwobodo/census-tracts-for-the-san-diego-ca-2017
- Download and unzip
- Place in: `data/san-diego-census-2017/`

## Verify your setup

After downloading, run notebook `01_pedestrian_eda.ipynb` cell 2. If it loads without `FileNotFoundError`, you're set.