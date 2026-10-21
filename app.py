import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="Global Conflict Tracker", layout="wide")

st.title("🌍 Global Conflict & Geopolitical Event Tracker")
st.markdown("An interactive platform tracking global conflicts and geopolitical developments.")

# Load Data
@st.cache_data
def load_data():
    return pd.read_csv("conflicts.csv")

df = load_data()

# Sidebar Filter Controls
st.sidebar.header("Filter Options")
selected_type = st.sidebar.multiselect(
    "Select Event Type",
    options=df["Type"].unique(),
    default=df["Type"].unique()
)

filtered_df = df[df["Type"].isin(selected_type)]

# Layout Setup
col1, col2 = st.columns([3, 1])

with col1:
    st.subheader("Global Hotspots Map")
    # OpenStreetMap tiles (Free, no API key required)
    m = folium.Map(location=[20.0, 0.0], zoom_start=2, tiles="OpenStreetMap")

    for _, row in filtered_df.iterrows():
        color = "red" if row["Type"] == "Armed Conflict" else "orange" if row["Type"] == "Civil War" else "blue"
        folium.Marker(
            location=[row["Latitude"], row["Longitude"]],
            popup=f"<b>{row['Location']}</b><br>Type: {row['Type']}<br>Status: {row['Status']}",
            tooltip=row["Location"],
            icon=folium.Icon(color=color)
        ).add_to(m)

    st_folium(m, width=800, height=450)

with col2:
    st.subheader("Data Summary")
    st.write(f"Total Active Events Displayed: **{len(filtered_df)}**")
    st.dataframe(filtered_df[["Location", "Type", "Status"]], use_container_width=True)