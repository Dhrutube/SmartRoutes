import streamlit as st

st.set_page_config(page_title="SmartRoutes", layout="wide")

st.title("SmartRoutes — San Diego MTS")

tab1, tab2, tab3 = st.tabs(["Pedestrian Heatmap", "Demand Score", "MTS Combined"])

with tab1:
    with open("san_diego_heatmap.html", "r") as f:
        st.components.v1.html(f.read(), height=700, scrolling=False)

with tab2:
    with open("demand_score_map.html", "r") as f:
        st.components.v1.html(f.read(), height=700, scrolling=False)

with tab3:
    with open("mts_combined_map.html", "r") as f:
        st.components.v1.html(f.read(), height=700, scrolling=False)