#!/usr/bin/env python
# coding: utf-8

# In[8]:


import pandas as pd, geopandas as gpd, folium
from shapely.geometry import LineString

merged = gpd.read_parquet("data/processed/demand.parquet")

shapes = pd.read_csv("data/shapes.txt")
lines = (shapes.sort_values(["shape_id", "shape_pt_sequence"])
               .groupby("shape_id")
               .apply(lambda g: LineString(zip(g["shape_pt_lon"], g["shape_pt_lat"]))
                      if len(g) >= 2 else None)
               .dropna()
               .reset_index(name="geometry"))
routes_gdf = gpd.GeoDataFrame(lines, geometry="geometry", crs="EPSG:4326")
print(len(routes_gdf), "route shapes")


# In[9]:


# thin to one line per route using the route<->shape link in trips.txt
trips = pd.read_csv("data/trips.txt", dtype={"route_id": str, "shape_id": str})
rep = trips.drop_duplicates("route_id")[["route_id", "shape_id"]]

routes_gdf["shape_id"] = routes_gdf["shape_id"].astype(str)
routes_thin = (routes_gdf.merge(rep, on="shape_id", how="inner")
                         .drop_duplicates("route_id"))
print(len(routes_thin), "routes (thinned from", len(routes_gdf), "shapes)")


# In[10]:


m = merged.explore(column="demand_score", cmap="YlOrRd", tiles="CartoDB positron",
                   legend=True, tooltip=["GEOID", "total_pop", "total_jobs", "demand_score"],
                   name="Demand")
routes_thin.explore(m=m, color="#13335c",
                    style_kwds={"weight": 2, "opacity": 0.8}, name="Bus routes")
folium.LayerControl().add_to(m)
m.save("outputs/demand_with_routes.html")
print("saved overlay map")


# In[11]:


import numpy as np
from sklearn.cluster import DBSCAN

# count MTS stops per tract (a simple service measure)
stops = pd.read_csv("data/stops.txt")
stops_gdf = gpd.GeoDataFrame(
    stops, geometry=gpd.points_from_xy(stops.stop_lon, stops.stop_lat), crs="EPSG:4326")
joined = gpd.sjoin(stops_gdf, merged[["GEOID", "geometry"]], predicate="within")
merged = merged.merge(joined.groupby("GEOID").size().rename("n_stops"),
                      on="GEOID", how="left")
merged["n_stops"] = merged["n_stops"].fillna(0)

# underserved = top-30% demand AND below-median stop count
hi_demand   = merged["demand_score"] > merged["demand_score"].quantile(0.70)
low_service = merged["n_stops"] <= merged["n_stops"].median()
underserved = merged[hi_demand & low_service].copy()
print(len(underserved), "underserved tracts")


# In[12]:


# MTS only covers central/south county; restrict to within ~3 km of an MTS route
service = routes_thin.to_crs("EPSG:3857").buffer(3000).unary_union
service_gdf = gpd.GeoDataFrame(geometry=[service], crs="EPSG:3857").to_crs("EPSG:4326")
in_mts = merged[merged.intersects(service_gdf.geometry.iloc[0])]

hi_demand   = in_mts["demand_score"] > in_mts["demand_score"].quantile(0.70)
low_service = in_mts["n_stops"] <= in_mts["n_stops"].median()
underserved = in_mts[hi_demand & low_service].copy()
print(len(underserved), "underserved tracts within MTS service area")


# In[13]:


# project to meters so distances are real, then group tracts within ~2 km
cent = underserved.to_crs("EPSG:3857").geometry.centroid
underserved["zone"] = DBSCAN(eps=2000, min_samples=2).fit_predict(np.c_[cent.x, cent.y])
print(underserved["zone"].value_counts())   # zone -1 = isolated/noise


# In[14]:


u = underserved[underserved["zone"] >= 0]   # drop the isolated ones
m = merged.explore(column="demand_score", cmap="YlOrRd", tiles="CartoDB positron",
                   legend=True, name="Demand")
u.explore(m=m, column="zone", categorical=True, cmap="tab10",
          style_kwds={"fillOpacity": 0.75}, name="Underserved zones")
routes_thin.explore(m=m, color="#13335c", style_kwds={"weight": 2, "opacity": 0.8}, name="Routes")
folium.LayerControl().add_to(m)
m.save("outputs/underserved_zones.html")
print("saved")


# In[15]:


cols = ["GEOID", "NAME", "total_pop", "total_jobs", "n_stops", "demand_score", "zone"]
print(underserved[underserved["zone"] >= 0][cols]
      .sort_values(["zone", "demand_score"], ascending=[True, False])
      .to_string(index=False))


# In[ ]:





# In[ ]:




