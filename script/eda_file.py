# %%
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Set a clean style for our visualizations
sns.set_theme(style="whitegrid")
print("Libraries imported successfully!")

# %%
# 1. Load the Pedestrian Data
pedestrians_df = pd.read_csv('data/cityiq.io-pedestrians-san_diego-1/data/pedestrians.csv')
segments_df = pd.read_csv('data/cityiq.io-pedestrians-san_diego-1/segments.csv')

print(f"Pedestrians Data Shape: {pedestrians_df.shape}")
print(f"Segments Data Shape: {segments_df.shape}")

# 2. Load the Transit Data (just stops and routes for now)
stops_df = pd.read_csv('data/MTS Data/stops.txt')
routes_df = pd.read_csv('data/MTS Data/routes.txt')

print(f"\nMTS Stops Shape: {stops_df.shape}")
print(f"MTS Routes Shape: {routes_df.shape}")

# 3. Take a peek at the first 5 rows of the pedestrian data
display(pedestrians_df.head())

# %%
# 1. Load the Pedestrian Data
pedestrians_df = pd.read_csv('data/cityiq.io-pedestrians-san_diego-1/data/pedestrians.csv')
# Updated path below to include the /notebooks/ folder!
segments_df = pd.read_csv('data/cityiq.io-pedestrians-san_diego-1/notebooks/segments.csv')

print(f"Pedestrians Data Shape: {pedestrians_df.shape}")
print(f"Segments Data Shape: {segments_df.shape}")

# 2. Load the Transit Data (just stops and routes for now)
stops_df = pd.read_csv('data/MTS Data/stops.txt')
routes_df = pd.read_csv('data/MTS Data/routes.txt')

print(f"\nMTS Stops Shape: {stops_df.shape}")
print(f"MTS Routes Shape: {routes_df.shape}")

# 3. Take a peek at the first 5 rows of the pedestrian data
display(pedestrians_df.head())

# %%
# 1. Check the data types to see if dates/times are currently just strings (objects)
print("--- Pedestrian Data Info ---")
pedestrians_df.info()

print("\n--- Missing Values Check ---")
# 2. Count how many empty cells exist in each column
missing_values = pedestrians_df.isnull().sum()
print(missing_values[missing_values > 0]) # Only show columns that actually have missing data

# 3. Look at the basic statistical spread of our numbers
display(pedestrians_df.describe())

# %%
# Convert timestamp from string to actual datetime objects
print("Converting timestamps... this may take a minute or two...")
pedestrians_df['timestamp'] = pd.to_datetime(pedestrians_df['timestamp'])

# Extract the hour and day of the week to make plotting easier later
pedestrians_df['hour'] = pedestrians_df['timestamp'].dt.hour
pedestrians_df['day_of_week'] = pedestrians_df['timestamp'].dt.day_name()

print("Timestamps converted successfully!")
display(pedestrians_df[['timestamp', 'hour', 'day_of_week']].head())

# %%
# 1. Group the data by hour and calculate the average count
print("Calculating hourly averages...")
hourly_counts = pedestrians_df.groupby('hour')['count'].mean().reset_index()

# 2. Set up the figure size
plt.figure(figsize=(12, 6))

# 3. Create a bar plot using Seaborn
sns.barplot(data=hourly_counts, x='hour', y='count', palette='magma')

# 4. Add labels and a title to make it readable
plt.title('Average Pedestrian Traffic by Hour of the Day (San Diego)', fontsize=16)
plt.xlabel('Hour of the Day (0 = Midnight, 23 = 11 PM)', fontsize=12)
plt.ylabel('Average Pedestrian Count', fontsize=12)

# 5. Display the plot
plt.show()

# %%
import geopandas as gpd
import pandas as pd
from shapely import wkt
import matplotlib.pyplot as plt
import seaborn as sns
import folium
from folium.plugins import HeatMapWithTime

# %%
%pip install folium

# %%
import geopandas as gpd
import pandas as pd
from shapely import wkt
import matplotlib.pyplot as plt
import seaborn as sns
import folium
from folium.plugins import HeatMapWithTime

# %%
# 1. Load your datasets (Adjust file paths if needed)
peds_df = pd.read_csv('data/cityiq.io-pedestrians-san_diego-1/data/pedestrians.csv')
segs_df = pd.read_csv('data/cityiq.io-pedestrians-san_diego-1/data/segments.csv')

# 2. Merge the counts with the geographic segments 
# Note: Check your dataframes to ensure 'locationUid' is the correct shared ID column
df_merged = pd.merge(peds_df, segs_df, on='locationUid')

# 3. Extract Latitude and Longitude from the WKT geometry
# We will use the centroid (middle point) of each walkway segment for the heat points
df_merged['geometry'] = df_merged['geometry'].apply(wkt.loads) # Change 'geometry' to your WKT column name if different
gdf = gpd.GeoDataFrame(df_merged, geometry='geometry')

# Extract Lat/Lon
df_merged['lat'] = gdf.geometry.centroid.y
df_merged['lon'] = gdf.geometry.centroid.x

# 4. Ensure your 'hour' column exists (based on your bar chart, you likely have this)
# If not, uncomment and adapt this line:
# df_merged['hour'] = pd.to_datetime(df_merged['time']).dt.hour

# %%
print("Pedestrians columns:", peds_df.columns.tolist())
print("Segments columns:", segs_df.columns.tolist())

# %%
# 1. Load your datasets
peds_df = pd.read_csv('data/cityiq.io-pedestrians-san_diego-1/data/pedestrians.csv')
segs_df = pd.read_csv('data/cityiq.io-pedestrians-san_diego-1/data/segments.csv')

# 2. FIX THE DATA TYPES BEFORE MERGING
# Convert both to strings, and remove any accidental '.0' from the float numbers
peds_df['locationuid'] = peds_df['locationuid'].astype(str).str.replace(r'\.0$', '', regex=True)
segs_df['roadsegid'] = segs_df['roadsegid'].astype(str).str.replace(r'\.0$', '', regex=True)

# 3. Merge using the cleaned column names
df_merged = pd.merge(peds_df, segs_df, left_on='locationuid', right_on='roadsegid')

# Rename 'count_x' back to 'count'
df_merged = df_merged.rename(columns={'count_x': 'count'})

# 4. Extract Latitude and Longitude from the WKT geometry
df_merged['geometry'] = df_merged['geometry'].apply(wkt.loads) 
gdf = gpd.GeoDataFrame(df_merged, geometry='geometry')

# Extract Lat/Lon from the centroid
df_merged['lat'] = gdf.geometry.centroid.y
df_merged['lon'] = gdf.geometry.centroid.x

# 5. Create the 'hour' column using your 'timestamp' column
df_merged['hour'] = pd.to_datetime(df_merged['timestamp']).dt.hour

print("Merge successful! You have", len(df_merged), "rows ready to map.")

# %%
# Let's peek at the first 5 IDs from both datasets to see how they differ
print("Pedestrian IDs:")
print(peds_df['locationuid'].head().tolist())

print("\nSegment IDs:")
print(segs_df['roadsegid'].head().tolist())

# %%
import os

# List all files in your dataset folder
folder_path = 'data/cityiq.io-pedestrians-san_diego-1/data/'
files = os.listdir(folder_path)
print("Files in my dataset folder:", files)

# %%
import geopandas as gpd
import pandas as pd
from shapely import wkt
import folium
from folium.plugins import HeatMapWithTime

# 1. Load just the segments file (it already has our counts and geometry!)
segs_df = pd.read_csv('data/cityiq.io-pedestrians-san_diego-1/data/segments.csv')

# 2. Extract Latitude and Longitude from the WKT string
segs_df['geometry'] = segs_df['geometry'].apply(wkt.loads) 
gdf = gpd.GeoDataFrame(segs_df, geometry='geometry')

# We'll use the centroid (middle point) of each segment for our heatmap
segs_df['lat'] = gdf.geometry.centroid.y
segs_df['lon'] = gdf.geometry.centroid.x

# 3. Group the data by "Time of Day" (tod) and get the average pedestrian count
grouped = segs_df.groupby(['tod', 'lat', 'lon'])['count'].mean().reset_index()

## Create a manual list in the exact chronological order you want the slider to play
time_periods = ['morning', 'lunch', 'afternoon', 'evening', 'night']

# 4. Format for Folium's HeatMapWithTime
heat_data = []
time_index = []

for time_period in time_periods:
    # Filter for the current time period
    time_data = grouped[grouped['tod'] == time_period]
    
    # Create a list of [lat, lon, weight] 
    locations_with_weight = time_data[['lat', 'lon', 'count']].values.tolist()
    
    heat_data.append(locations_with_weight)
    
    # The label for the slider (e.g., 'morning', 'afternoon')   
    time_index.append(f"Time: {time_period}")

# 5. Render the Map!
san_diego_coords = [32.7157, -117.1611]
m = folium.Map(location=san_diego_coords, zoom_start=13, tiles='CartoDB positron')

HeatMapWithTime(
    data=heat_data,
    index=time_index,
    radius=15,          
    auto_play=True,     
    max_opacity=0.8
).add_to(m)

# Save the map to an HTML file instead of displaying it in the notebook
m.save('san_diego_heatmap.html')

# %%



