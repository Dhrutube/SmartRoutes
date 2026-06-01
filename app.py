import streamlit as st

st.set_page_config(page_title="SmartRoutes", layout="wide")

st.title("SmartRoutes — San Diego MTS")
st.markdown("🚌 A geospatial data project aimed at improving San Diego MTS bus routes by analyzing population density and pedestrian foot-traffic.")

tab1, tab2 = st.tabs(["Pedestrian Heatmap", "Map of Underserved Zones"])

with tab1:
    with open("Outputs/san_diego_heatmap.html", "r") as f:
        st.components.v1.html(f.read(), height=700, scrolling=False)

with tab2:
    with open("html_visualizations/underserved_zones_map.html", "r") as f:
        st.components.v1.html(f.read(), height=700, scrolling=False)