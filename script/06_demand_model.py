#!/usr/bin/env python
# coding: utf-8

# In[1]:


import pandas as pd, geopandas as gpd, urllib.request, ssl, certifi, io

gdf = gpd.read_parquet("data/processed/census_clean.parquet")

url = "https://lehd.ces.census.gov/data/lodes/LODES7/ca/wac/ca_wac_S000_JT00_2019.csv.gz"
ctx = ssl.create_default_context(cafile=certifi.where())
with urllib.request.urlopen(url, context=ctx) as resp:
    wac = pd.read_csv(io.BytesIO(resp.read()), compression="gzip", dtype={"w_geocode": str})

sd = wac[wac["w_geocode"].str.startswith("06073")].copy()
sd["GEOID"] = sd["w_geocode"].str[:11]
jobs = (sd.groupby("GEOID", as_index=False)["C000"]
          .sum().rename(columns={"C000": "total_jobs"}))
print(jobs.shape[0], "tracts with jobs")


# In[2]:


merged = gdf.merge(jobs, on="GEOID", how="left")
merged["total_jobs"] = merged["total_jobs"].fillna(0)
print("joined:", merged["total_jobs"].gt(0).sum(), "/", len(merged))

def norm(s):
    return (s - s.min()) / (s.max() - s.min())

merged["pop_norm"]  = norm(merged["total_pop"].astype(float))
merged["jobs_norm"] = norm(merged["total_jobs"])

w_pop, w_jobs = 0.5, 0.5
merged["demand_score"] = w_pop * merged["pop_norm"] + w_jobs * merged["jobs_norm"]


# In[3]:


m = merged.explore(column="demand_score", cmap="YlOrRd", tiles="CartoDB positron",
                   legend=True, tooltip=["GEOID", "total_pop", "total_jobs", "demand_score"])
m.save("outputs/demand_score_map.html")
merged.to_parquet("data/processed/demand.parquet")
print("saved demand layer")


# In[ ]:




