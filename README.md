# SmartRoutes — San Diego MTS

🚌 A geospatial data project that analyzes how well San Diego's Metropolitan
Transit System (MTS) serves the region, and surfaces **underserved zones** where
transit supply does not keep up with demand.

SmartRoutes combines U.S. Census demographics, GTFS transit-stop locations, and
CityIQ pedestrian foot-traffic to score each census tract on a *need vs. supply*
gap, then clusters high-gap tracts into candidate zones for new or improved bus
routes. The results are presented as interactive maps and charts, both in a
Streamlit web app and as standalone HTML files.

## What it does

- **Income distribution** — median household income by census tract (choropleth)
  and the count of tracts per income bracket.
- **Transit stop density** — transit stops per km² by tract, plus a dot map of
  every stop colored by agency.
- **Income vs. transit density** — scatter with OLS fit, marginal histograms, and
  a low- vs. high-income boxplot, with correlation/significance statistics
  (Pearson, Spearman, Welch t-test, Mann–Whitney).
- **Underserved zones** — a composite *need index* (population density, renter
  share, and inverse income) compared against transit supply to compute a
  `gap_score`. Tracts above the 75th-percentile gap are flagged underserved and
  clustered into geographic zones via hierarchical clustering.

## Project structure

```
SmartRoutes/
├── app.py                              # Streamlit web app (3 interactive tabs)
├── script/
│   └── generate_html_visualizations.py # Builds the standalone HTML maps/charts
├── html_visualizations/                # Generated interactive HTML (committed)
│   ├── index.html                      # Landing page linking every viz
│   ├── san_diego_heatmap.html
│   ├── underserved_zones_map_income.html
│   ├── underserved_zones_map_density.html
│   └── ...
├── output_csvs/                        # Derived CSVs (income & stop-density)
├── data/                               # Raw datasets (gitignored — see below)
│   ├── cityiq.io-pedestrians-san_diego-1/
│   ├── san-diego-census-geopandas/
│   └── transit-stops-gtfs/
├── requirements.txt
└── README.md
```

> **Note:** `data/` and the `.smartroutes/` virtual environment are listed in
> `.gitignore` and are **not** checked into the repository. You must supply the
> raw datasets locally (see [Data](#data)). The pre-generated files in
> `html_visualizations/` let the Streamlit app run without regenerating anything.

## Data

The pipeline expects three datasets under `data/`:

| Dataset | Path | Source |
| --- | --- | --- |
| Census tracts (income, population, housing) | `data/san-diego-census-geopandas/data/San Diego.csv` | U.S. Census / GeoPandas |
| Transit stops (GTFS) | `data/transit-stops-gtfs/data/Transit_Stops_GTFS.csv` | San Diego MTS GTFS feed |
| Pedestrian foot-traffic | `data/cityiq.io-pedestrians-san_diego-1/data/pedestrians.csv` | CityIQ |

The generator also reads two derived CSVs from `output_csvs/`:

- `san_diego_income_distribution.csv` — `GEOID`, `median_hh_income`, `income_bracket`, `total_pop`
- `san_diego_transit_stop_density.csv` — `GEOID`, `num_stops`, `area_km2`, `stops_per_km2`

These are produced by the exploratory notebooks bundled with each dataset under
`data/*/notebook/`.

## Setup

Requires **Python 3.11+** (developed on 3.14).

```bash
# 1. Clone
git clone <your-repo-url> SmartRoutes
cd SmartRoutes

# 2. Create and activate a virtual environment
python -m venv .smartroutes

# Windows (PowerShell)
.smartroutes\Scripts\Activate.ps1
# macOS / Linux
source .smartroutes/bin/activate

# 3. Install dependencies
pip install -r requirements.txt
```

## Running locally

### Streamlit app

```bash
streamlit run app.py
```

This launches the web app (default `http://localhost:8501`) with three tabs:
pedestrian heatmap, underserved zones by income, and underserved zones by
density. It reads the pre-generated files in `html_visualizations/`, so no data
or regeneration step is required.

### Regenerating the visualizations

To rebuild the maps and charts from the raw data (requires the datasets in
`data/` and the derived CSVs in `output_csvs/`):

```bash
python script/generate_html_visualizations.py
```

The script writes interactive HTML for every chart and map, prints progress for
each of the four analysis stages, and lists the files it produced.

## Deployment

### Streamlit Community Cloud (recommended)

1. Push the repository to GitHub (`html_visualizations/` is committed, so the app
   has everything it needs to render).
2. Go to [share.streamlit.io](https://share.streamlit.io) and connect your
   GitHub account.
3. Create a new app pointing at this repo, branch `main`, with **main file**
   `app.py`.
4. Streamlit Cloud installs `requirements.txt` automatically and deploys. Pushes
   to `main` redeploy the app.

### Docker

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

```bash
docker build -t smartroutes .
docker run -p 8501:8501 smartroutes
```

### Static hosting (HTML only)

The contents of `html_visualizations/` are fully self-contained (Plotly/Leaflet
load from CDN). Serve that folder from any static host (GitHub Pages, Netlify,
S3, etc.) and open `index.html` for a linked index of every visualization.

## Tech stack

- **Streamlit** — web app
- **pandas / numpy** — data wrangling
- **GeoPandas / Shapely** — geospatial geometry handling
- **SciPy** — statistics and hierarchical clustering
- **Plotly** — interactive charts
- **Folium** (Leaflet.js) — interactive maps and choropleths
