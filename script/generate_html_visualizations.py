"""
Generate interactive HTML versions of every visualization in the four notebooks.

Outputs (one file each) into ./html_viz/:
  income_choropleth.html             — median household income by tract
  income_bracket_distribution.html   — # tracts per income bracket
  transit_density_choropleth.html    — transit stops per km^2 by tract
  transit_stops_map.html             — every transit stop as a dot
  income_vs_density_scatter.html     — scatter + OLS line (incl. histograms)
  income_vs_density_boxplot.html     — boxplot, low- vs high-income halves
  underserved_zones_map.html         — clustered underserved zones
  underserved_gap_distribution.html  — gap-score histogram + need/supply scatter
"""

from pathlib import Path
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely import wkt
from scipy import stats
from scipy.cluster.hierarchy import linkage, fcluster

import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import folium
from folium.features import GeoJsonTooltip

import warnings
warnings.simplefilter(action='ignore', category=Warning)

ROOT = Path(__file__).parent
OUT  = ROOT / 'html_viz'
OUT.mkdir(exist_ok=True)

CENSUS_CSV  = ROOT / 'data' / 'san-diego-census-geopandas' / 'data' / 'San Diego.csv'
STOPS_CSV   = ROOT / 'data' / 'transit-stops-gtfs' / 'data' / 'Transit_Stops_GTFS.csv'
INCOME_CSV  = ROOT / 'output_csvs' / 'san_diego_income_distribution.csv'
DENSITY_CSV = ROOT / 'output_csvs' / 'san_diego_transit_stop_density.csv'

# ---------------------------------------------------------------------------
# Shared: load tracts in WGS84 for folium
# ---------------------------------------------------------------------------
print('Loading census tracts...')
tracts_df = pd.read_csv(CENSUS_CSV, delimiter=',', encoding='ISO-8859-2')
tracts_gdf = gpd.GeoDataFrame(tracts_df.copy())
tracts_gdf['geometry'] = tracts_gdf['geometry'].apply(wkt.loads)
tracts_gdf = tracts_gdf.set_geometry('geometry')
# The WKT coords are Web Mercator, not the labeled CRS.
tracts_gdf = tracts_gdf.set_crs('EPSG:3857', allow_override=True)
tracts_wgs = tracts_gdf.to_crs('EPSG:4326')
tracts_gdf['area_name'] = tracts_gdf['NAME'].str.replace(
    ', San Diego County, California', '', regex=False)
tracts_wgs['area_name'] = tracts_gdf['area_name']

SD_CENTER = [32.85, -117.05]

# ===========================================================================
# 1. INCOME DISTRIBUTION
# ===========================================================================
print('1/4  Income distribution...')
income = pd.read_csv(INCOME_CSV)
income['GEOID'] = income['GEOID'].astype(str)

inc_gdf = tracts_wgs[['GEOID', 'area_name', 'geometry']].copy()
inc_gdf['GEOID'] = inc_gdf['GEOID'].astype(str)
inc_gdf = inc_gdf.merge(
    income[['GEOID', 'median_hh_income', 'income_bracket', 'total_pop']],
    on='GEOID', how='left')

# Choropleth (folium)
m = folium.Map(location=SD_CENTER, zoom_start=10, tiles='cartodbpositron')
folium.Choropleth(
    geo_data=inc_gdf.__geo_interface__,
    data=inc_gdf,
    columns=['GEOID', 'median_hh_income'],
    key_on='feature.properties.GEOID',
    fill_color='Reds',
    fill_opacity=0.75,
    line_opacity=0.3,
    nan_fill_color='#dddddd',
    legend_name='Median household income (USD)',
    name='Median household income',
).add_to(m)
folium.GeoJson(
    inc_gdf,
    style_function=lambda f: {'color': 'transparent', 'fillOpacity': 0},
    tooltip=GeoJsonTooltip(
        fields=['area_name', 'median_hh_income', 'income_bracket', 'total_pop'],
        aliases=['Tract:', 'Median income:', 'Bracket:', 'Population:'],
        localize=True, sticky=False),
    name='Hover details',
).add_to(m)
folium.LayerControl().add_to(m)
m.save(OUT / 'income_choropleth.html')

# Bracket bar chart (plotly)
bracket_labels = ['<$25k', '$25k–$50k', '$50k–$75k', '$75k–$100k',
                  '$100k–$150k', '$150k–$200k', '$200k+']
bracket_counts = (income['income_bracket']
                  .value_counts()
                  .reindex(bracket_labels)
                  .fillna(0)
                  .astype(int))
fig = px.bar(
    x=bracket_labels, y=bracket_counts.values,
    labels={'x': 'Income bracket', 'y': '# census tracts'},
    title='San Diego County — Census tracts per income bracket',
    color=bracket_counts.values, color_continuous_scale='Reds',
)
fig.update_layout(coloraxis_showscale=False, template='plotly_white')
fig.write_html(OUT / 'income_bracket_distribution.html', include_plotlyjs='cdn')

# ===========================================================================
# 2. TRANSIT STOP DENSITY  (+ raw stops map)
# ===========================================================================
print('2/4  Transit stop density...')
density = pd.read_csv(DENSITY_CSV)
density['GEOID'] = density['GEOID'].astype(str)

dens_gdf = tracts_wgs[['GEOID', 'area_name', 'geometry']].copy()
dens_gdf['GEOID'] = dens_gdf['GEOID'].astype(str)
dens_gdf = dens_gdf.merge(
    density[['GEOID', 'num_stops', 'area_km2', 'stops_per_km2']],
    on='GEOID', how='left')
dens_gdf['stops_per_km2'] = dens_gdf['stops_per_km2'].fillna(0)
dens_gdf['num_stops'] = dens_gdf['num_stops'].fillna(0).astype(int)

# Cap at the 99th percentile so dense urban tracts don't wash the rest out.
vmax = float(dens_gdf['stops_per_km2'].quantile(0.99))
dens_gdf['stops_per_km2_capped'] = dens_gdf['stops_per_km2'].clip(upper=vmax)

m = folium.Map(location=SD_CENTER, zoom_start=10, tiles='cartodbpositron')
folium.Choropleth(
    geo_data=dens_gdf.__geo_interface__,
    data=dens_gdf,
    columns=['GEOID', 'stops_per_km2_capped'],
    key_on='feature.properties.GEOID',
    fill_color='Blues',
    fill_opacity=0.8,
    line_opacity=0.3,
    nan_fill_color='#dddddd',
    legend_name=f'Transit stops per km² (capped at 99th pct ≈ {vmax:.1f})',
    name='Transit stop density',
).add_to(m)
folium.GeoJson(
    dens_gdf,
    style_function=lambda f: {'color': 'transparent', 'fillOpacity': 0},
    tooltip=GeoJsonTooltip(
        fields=['area_name', 'num_stops', 'area_km2', 'stops_per_km2'],
        aliases=['Tract:', '# stops:', 'Area (km²):', 'Stops / km²:'],
        localize=True),
).add_to(m)
folium.LayerControl().add_to(m)
m.save(OUT / 'transit_density_choropleth.html')

# Raw stops dot map
print('     stops dot map...')
stops_df = pd.read_csv(STOPS_CSV)
stops_df.columns = stops_df.columns.str.strip().str.lstrip('﻿')
stops_df = stops_df.dropna(subset=['stop_lat', 'stop_lon'])
fig = px.scatter_mapbox(
    stops_df, lat='stop_lat', lon='stop_lon',
    hover_name='stop_name', hover_data={'stop_agency': True, 'stop_id': True,
                                        'stop_lat': False, 'stop_lon': False},
    color='stop_agency', zoom=9, height=750,
    title=f'San Diego transit stops ({len(stops_df):,} total)',
)
fig.update_traces(marker=dict(size=5, opacity=0.7))
fig.update_layout(mapbox_style='carto-positron',
                  margin=dict(l=0, r=0, t=40, b=0),
                  legend_title='Agency')
fig.write_html(OUT / 'transit_stops_map.html', include_plotlyjs='cdn')

# ===========================================================================
# 3. INCOME vs TRANSIT DENSITY
# ===========================================================================
print('3/4  Income vs transit density...')
income_v = pd.read_csv(INCOME_CSV)
density_v = pd.read_csv(DENSITY_CSV)
df = income_v.merge(
    density_v[['GEOID', 'num_stops', 'area_km2', 'stops_per_km2']],
    on='GEOID', how='inner'
).dropna(subset=['median_hh_income', 'stops_per_km2'])

x = df['median_hh_income'].to_numpy()
y = df['stops_per_km2'].to_numpy()
slope, intercept, r, p, se = stats.linregress(x, y)
pearson  = stats.pearsonr(x, y)
spearman = stats.spearmanr(x, y)

# Scatter + regression + marginal histograms.
fig = px.scatter(
    df, x='median_hh_income', y='stops_per_km2',
    marginal_x='histogram', marginal_y='histogram',
    opacity=0.55, trendline='ols', trendline_color_override='#e4572e',
    hover_data={'area': True, 'num_stops': True, 'GEOID': True},
    labels={'median_hh_income': 'Median household income (USD)',
            'stops_per_km2': 'Transit stops per km²'},
    title=(f'Income vs transit stop density  '
           f'(Pearson r={pearson.statistic:.3f}, p={pearson.pvalue:.2e} · '
           f'Spearman ρ={spearman.statistic:.3f}, p={spearman.pvalue:.2e} · '
           f'R²={r ** 2:.3f})'),
)
fig.update_layout(template='plotly_white', height=700)
fig.write_html(OUT / 'income_vs_density_scatter.html', include_plotlyjs='cdn')

# Boxplot: low- vs high-income halves
median_inc = df['median_hh_income'].median()
df['income_half'] = np.where(df['median_hh_income'] <= median_inc,
                             f'Lower (≤ ${median_inc:,.0f})',
                             f'Higher (> ${median_inc:,.0f})')
low  = df.loc[df['income_half'].str.startswith('Lower'),  'stops_per_km2']
high = df.loc[df['income_half'].str.startswith('Higher'), 'stops_per_km2']
ttest = stats.ttest_ind(low, high, equal_var=False)
mwu   = stats.mannwhitneyu(low, high, alternative='two-sided')

fig = px.box(
    df, x='income_half', y='stops_per_km2', points='outliers',
    color='income_half',
    color_discrete_sequence=['#4c78a8', '#e4572e'],
    labels={'income_half': 'Income half (split at median)',
            'stops_per_km2': 'Transit stops per km²'},
    title=(f'Transit density by income half · '
           f'Welch t p={ttest.pvalue:.2e}, Mann–Whitney p={mwu.pvalue:.2e}'),
)
fig.update_layout(template='plotly_white', showlegend=False, height=600)
fig.write_html(OUT / 'income_vs_density_boxplot.html', include_plotlyjs='cdn')

# ===========================================================================
# 4. UNDERSERVED ZONES
# ===========================================================================
print('4/4  Underserved zones...')
UNDERSERVED_Q = 0.75
ZONE_EPS_M = 1200
METERS_CRS = 'EPSG:32611'

census  = pd.read_csv(CENSUS_CSV, delimiter=',', encoding='ISO-8859-2')
density2 = pd.read_csv(DENSITY_CSV)

df2 = census.merge(
    density2[['GEOID', 'num_stops', 'area_km2', 'stops_per_km2']],
    on='GEOID', how='inner')
gdf2 = gpd.GeoDataFrame(df2, geometry=df2['geometry'].apply(wkt.loads), crs='EPSG:3857')

gdf2['pop_density']  = gdf2['total_pop'] / gdf2['area_km2']
gdf2['renter_share'] = gdf2['total_rented'] / gdf2['total_housing_units']
need_cols = ['pop_density', 'renter_share', 'median_hh_income']
gdf2 = gdf2.dropna(subset=need_cols + ['stops_per_km2']).copy()

def zscore(s):
    s = s.astype(float)
    return (s - s.mean()) / s.std(ddof=0)

gdf2['need_index'] = pd.concat([
    zscore(gdf2['pop_density']),
    zscore(gdf2['renter_share']),
    zscore(-gdf2['median_hh_income']),
], axis=1).mean(axis=1)
gdf2['z_need']    = zscore(gdf2['need_index'])
gdf2['z_supply']  = zscore(np.log1p(gdf2['stops_per_km2']))
gdf2['gap_score'] = gdf2['z_need'] - gdf2['z_supply']

threshold = gdf2['gap_score'].quantile(UNDERSERVED_Q)
gdf2['underserved'] = gdf2['gap_score'] >= threshold

under = gdf2[gdf2['underserved']].copy()
cent = under.geometry.to_crs(METERS_CRS).centroid
coords = np.c_[cent.x.to_numpy(), cent.y.to_numpy()]
if len(coords) > 1:
    Z = linkage(coords, method='single')
    zone_ids = fcluster(Z, t=ZONE_EPS_M, criterion='distance')
else:
    zone_ids = np.ones(len(coords), dtype=int)
under['zone_id'] = zone_ids
sizes = under['zone_id'].value_counts()
under['zone_size'] = under['zone_id'].map(sizes)
under['zone_gap']  = under.groupby('zone_id')['gap_score'].transform('mean')

# Distribution + need/supply scatter (plotly subplots)
fig = make_subplots(rows=1, cols=2, subplot_titles=(
    f'Gap-score distribution (threshold q={UNDERSERVED_Q} = {threshold:.2f})',
    'Need vs supply (red = underserved)'))
fig.add_trace(go.Histogram(x=gdf2['gap_score'], nbinsx=40,
                           marker_color='#4c78a8', name='gap_score'),
              row=1, col=1)
fig.add_vline(x=threshold, line_color='#e4572e', line_width=2, row=1, col=1)
fig.add_trace(
    go.Scatter(
        x=gdf2['z_supply'], y=gdf2['z_need'], mode='markers',
        marker=dict(
            color=np.where(gdf2['underserved'], '#e4572e', '#bbbbbb'),
            size=6, opacity=0.7,
        ),
        text=gdf2['NAME'].str.replace(', San Diego County, California', '', regex=False),
        hovertemplate='%{text}<br>z_supply=%{x:.2f}<br>z_need=%{y:.2f}<extra></extra>',
        name='tracts',
    ),
    row=1, col=2,
)
fig.update_xaxes(title_text='gap_score (z_need − z_supply)', row=1, col=1)
fig.update_yaxes(title_text='# tracts', row=1, col=1)
fig.update_xaxes(title_text='z_supply (transit stops)', row=1, col=2)
fig.update_yaxes(title_text='z_need (demand)', row=1, col=2)
fig.update_layout(template='plotly_white', showlegend=False, height=520,
                  title_text='Underserved transit zones — supply gap diagnostics')
fig.write_html(OUT / 'underserved_gap_distribution.html', include_plotlyjs='cdn')

# Zones map (folium)
gdf2_wgs  = gdf2.to_crs('EPSG:4326').copy()
gdf2_wgs['area_name'] = gdf2_wgs['NAME'].str.replace(
    ', San Diego County, California', '', regex=False)
under_wgs = gdf2_wgs.merge(under[['GEOID', 'zone_id', 'zone_size', 'zone_gap']],
                           on='GEOID', how='inner')

multi = under_wgs[under_wgs['zone_size'] >= 2].copy()
solo  = under_wgs[under_wgs['zone_size'] == 1].copy()

zone_order = (multi.groupby('zone_id')['zone_gap'].first()
              .sort_values(ascending=False).index.tolist())
tab20 = ['#1f77b4','#aec7e8','#ff7f0e','#ffbb78','#2ca02c','#98df8a',
         '#d62728','#ff9896','#9467bd','#c5b0d5','#8c564b','#c49c94',
         '#e377c2','#f7b6d2','#7f7f7f','#c7c7c7','#bcbd22','#dbdb8d',
         '#17becf','#9edae5']
zone_color = {zid: tab20[i % 20] for i, zid in enumerate(zone_order)}

m = folium.Map(location=SD_CENTER, zoom_start=10, tiles='cartodbpositron')

# All tracts as a soft background
folium.GeoJson(
    gdf2_wgs[['GEOID', 'area_name', 'gap_score', 'stops_per_km2', 'geometry']],
    name='all tracts',
    style_function=lambda f: {'fillColor': '#eeeeee', 'color': 'white',
                               'weight': 0.3, 'fillOpacity': 0.5},
    tooltip=GeoJsonTooltip(
        fields=['area_name', 'gap_score', 'stops_per_km2'],
        aliases=['Tract:', 'Gap score:', 'Stops/km²:'], localize=True),
).add_to(m)

# Multi-tract underserved zones
for zid in zone_order:
    grp = multi[multi['zone_id'] == zid]
    folium.GeoJson(
        grp[['GEOID', 'area_name', 'gap_score', 'zone_id', 'zone_gap', 'geometry']],
        name=f'zone {zid} (mean gap {grp["zone_gap"].iloc[0]:.2f})',
        style_function=lambda f, c=zone_color[zid]: {
            'fillColor': c, 'color': 'black', 'weight': 0.6, 'fillOpacity': 0.75},
        tooltip=GeoJsonTooltip(
            fields=['area_name', 'gap_score', 'zone_id', 'zone_gap'],
            aliases=['Tract:', 'Gap:', 'Zone:', 'Zone mean gap:'], localize=True),
    ).add_to(m)

# Isolated underserved tracts
folium.GeoJson(
    solo[['GEOID', 'area_name', 'gap_score', 'geometry']],
    name='isolated underserved tracts',
    style_function=lambda f: {'fillColor': '#999999', 'color': 'black',
                               'weight': 0.4, 'fillOpacity': 0.7},
    tooltip=GeoJsonTooltip(
        fields=['area_name', 'gap_score'],
        aliases=['Tract:', 'Gap:'], localize=True),
).add_to(m)

folium.LayerControl(collapsed=False).add_to(m)
m.save(OUT / 'underserved_zones_map.html')

# ---------------------------------------------------------------------------
# Index page
# ---------------------------------------------------------------------------
index_html = """<!doctype html>
<html><head><meta charset="utf-8"><title>SmartRoutes — HTML visualizations</title>
<style>
 body{font-family:system-ui,sans-serif;max-width:780px;margin:40px auto;padding:0 16px;color:#222}
 h1{margin-bottom:4px} .sub{color:#666;margin-bottom:28px}
 h2{margin-top:32px;border-bottom:1px solid #eee;padding-bottom:6px}
 ul{padding-left:18px} li{margin:6px 0} a{color:#0b65c2;text-decoration:none}
 a:hover{text-decoration:underline}
</style></head><body>
<h1>SmartRoutes — Interactive Visualizations</h1>
<div class="sub">HTML versions of every chart and map in the project notebooks.</div>

<h2>Income distribution</h2>
<ul>
  <li><a href="income_choropleth.html">Median household income choropleth</a></li>
  <li><a href="income_bracket_distribution.html">Census tracts per income bracket</a></li>
</ul>

<h2>Transit stops</h2>
<ul>
  <li><a href="transit_density_choropleth.html">Transit stop density choropleth</a></li>
  <li><a href="transit_stops_map.html">Every transit stop (colored by agency)</a></li>
</ul>

<h2>Income vs transit density</h2>
<ul>
  <li><a href="income_vs_density_scatter.html">Scatter + OLS fit + marginal histograms</a></li>
  <li><a href="income_vs_density_boxplot.html">Boxplot: low- vs high-income halves</a></li>
</ul>

<h2>Underserved zones</h2>
<ul>
  <li><a href="underserved_zones_map.html">Clustered underserved zones map</a></li>
  <li><a href="underserved_gap_distribution.html">Gap-score distribution + need/supply scatter</a></li>
</ul>
</body></html>
"""
(OUT / 'index.html').write_text(index_html, encoding='utf-8')

print(f'\nDone. {len(list(OUT.glob("*.html")))} HTML files written to {OUT}')
for p in sorted(OUT.glob('*.html')):
    print(' ', p.name)
