# SmartRoutes

Transit-equity analysis for San Diego County. The project joins US Census tract demographics with GTFS transit-stop data to ask one question: **are low-income, high-demand neighborhoods getting their fair share of transit service, and where are the biggest gaps?**

## Project layout

```
SmartRoutes/
├── data/                              # raw inputs (not all tracked)
│   ├── san-diego-census-geopandas/    # 2017 census tracts (WKT geometry + demographics)
│   ├── transit-stops-gtfs/            # GTFS stops for MTS, NCTD, etc.
│   └── cityiq.io-pedestrians-san_diego-1/
│
├── san-diego-income-distribution.ipynb     # 1. income distribution per tract
├── transit-stops-density.ipynb             # 2. transit stops per km² per tract
├── income-vs-transit-density-test.ipynb    # 3. statistical tests on the relationship
├── underserved-zones-clustering.ipynb      # 4. flag + cluster underserved zones
│
├── generate_html_visualizations.py    # rebuilds every chart/map as interactive HTML
├── output_csvs/                       # tract-level outputs (one row per GEOID)
└── html_viz/                          # interactive HTML versions of every viz
```

## Notebooks

### 1. [san-diego-income-distribution.ipynb](san-diego-income-distribution.ipynb)
Builds a per-tract income table from the 2017 census data, buckets each tract into income brackets (`<$25k` through `$200k+`), and renders a light-red → dark-red choropleth of median household income.

**Output:** [output_csvs/san_diego_income_distribution.csv](output_csvs/san_diego_income_distribution.csv)

### 2. [transit-stops-density.ipynb](transit-stops-density.ipynb)
Spatially joins every GTFS transit stop to the census tract it falls in, divides by the tract's area in km² (using EPSG:26946 so distances are real metres, not Web Mercator), and renders a light-blue → dark-blue choropleth with a 99th-percentile cap so dense downtown tracts don't wash out the rest.

**Output:** [output_csvs/san_diego_transit_stop_density.csv](output_csvs/san_diego_transit_stop_density.csv)

### 3. [income-vs-transit-density-test.ipynb](income-vs-transit-density-test.ipynb)
Joins the two tables above on `GEOID` and runs formal stats at α = 0.05:

- Pearson correlation (linear)
- Spearman rank correlation (monotonic, robust to skew)
- OLS slope + R²
- Welch t-test and Mann–Whitney U comparing the lower- vs higher-income halves at the median split

Includes a scatter + OLS fit and a boxplot.

### 4. [underserved-zones-clustering.ipynb](underserved-zones-clustering.ipynb)
Builds a per-tract supply-gap score and flags the worst-served quartile, then clusters them into actionable zones.

- **Need index** = mean of z-scored `pop_density`, `renter_share`, and `-median_hh_income`.
- **Supply** = z-scored `log1p(stops_per_km2)`.
- **Gap score** = `z_need − z_supply`. Tracts at/above the 75th percentile are flagged underserved.
- **Zones** = single-linkage clustering on underserved-tract centroids in UTM 11N (EPSG:32611) with a 1,200 m distance cutoff. Equivalent to DBSCAN with `min_samples=1`: chains of nearby underserved tracts collapse into one zone, isolated tracts stay as singletons.

**Output:** [output_csvs/san_diego_underserved_zones.csv](output_csvs/san_diego_underserved_zones.csv) — every tract with its `gap_score`, `underserved` flag, and `zone_id`.

## Interactive visualizations

Run [generate_html_visualizations.py](generate_html_visualizations.py) to rebuild every chart and map in the notebooks as a standalone HTML file:

```bash
python generate_html_visualizations.py
```

Outputs land in [html_viz/](html_viz/). Open [html_viz/index.html](html_viz/index.html) for the full index, or jump to a specific viz:

| File | What it shows |
|---|---|
| [income_choropleth.html](html_viz/income_choropleth.html) | Median household income by tract (folium) |
| [income_bracket_distribution.html](html_viz/income_bracket_distribution.html) | # tracts per income bracket (plotly bar) |
| [transit_density_choropleth.html](html_viz/transit_density_choropleth.html) | Transit stops per km² by tract, 99th-pct capped |
| [transit_stops_map.html](html_viz/transit_stops_map.html) | Every transit stop as a dot, colored by agency |
| [income_vs_density_scatter.html](html_viz/income_vs_density_scatter.html) | Scatter + OLS fit with marginal histograms |
| [income_vs_density_boxplot.html](html_viz/income_vs_density_boxplot.html) | Boxplot: low- vs high-income halves |
| [underserved_zones_map.html](html_viz/underserved_zones_map.html) | Clustered underserved zones (folium) |
| [underserved_gap_distribution.html](html_viz/underserved_gap_distribution.html) | Gap-score histogram + need/supply scatter |

## Data notes

- The census `geometry` column is labelled EPSG:26946 in the source but the coordinates are actually **EPSG:3857 (Web Mercator)**. The code re-tags the CRS before doing anything spatial — areas computed in Mercator would be badly distorted otherwise.
- All area-based math (stop density, population density) is done in EPSG:26946 (NAD83 / California zone 6, metres).
- Clustering distances are done in EPSG:32611 (UTM 11N, metres) for consistency over San Diego.

## Dependencies

Python 3 with `pandas`, `numpy`, `geopandas`, `shapely`, `scipy`, `matplotlib`, `plotly`, `folium`. A local venv lives at `.smartroutes/` (gitignored).
