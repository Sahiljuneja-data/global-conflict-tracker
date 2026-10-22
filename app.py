import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import plotly.express as px
import requests
import xml.etree.ElementTree as ET

st.set_page_config(
    page_title="Global Conflict & Geopolitical Intelligence Tracker",
    page_icon="🌍",
    layout="wide"
)

# Application Header
st.title("🌍 Global Conflict & Geopolitical Intelligence Tracker")
st.markdown("*Real-time geospatial intelligence, strategic impact assessments, and localized news feeds.*")

# 1. Load Expanded Hotspot Dataset
@st.cache_data
def load_data():
    return pd.read_csv("conflicts.csv")

df = load_data()

# 2. Live News Engine (GDELT API + RSS Fallback)
def fetch_rss_news(query, max_records=10):
    url = f"https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
    try:
        response = requests.get(url, headers=headers, timeout=8)
        if response.status_code == 200:
            root = ET.fromstring(response.content)
            events = []
            for item in root.findall(".//item")[:max_records]:
                title = item.find("title").text if item.find("title") is not None else "No Title"
                link = item.find("link").text if item.find("link") is not None else "#"
                pub_date = item.find("pubDate").text if item.find("pubDate") is not None else ""
                source_elem = item.find("source")
                source = source_elem.text if source_elem is not None else "Global News"
                events.append({"Title": title, "Source": source, "URL": link, "Date": pub_date})
            return pd.DataFrame(events)
    except Exception:
        pass
    return pd.DataFrame()

@st.cache_data(ttl=300)
def fetch_live_news(query):
    gdelt_url = "https://api.gdeltproject.org/api/v2/doc/doc"
    params = {
        "query": f"({query}) sourcelang:english",
        "mode": "artlist",
        "maxrecords": 10,
        "format": "json"
    }
    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
    
    try:
        response = requests.get(gdelt_url, params=params, headers=headers, timeout=6)
        if response.status_code == 200:
            articles = response.json().get("articles", [])
            if articles:
                events = [{
                    "Title": art.get("title"),
                    "Source": art.get("domain"),
                    "URL": art.get("url"),
                    "Date": art.get("seendate")
                } for art in articles]
                return pd.DataFrame(events), "GDELT Project API"
    except Exception:
        pass

    rss_df = fetch_rss_news(query=query)
    if not rss_df.empty:
        return rss_df, "Live Geopolitical RSS"

    return pd.DataFrame(), "No Active News"

# --- SIDEBAR CONTROLS ---
st.sidebar.header("🎯 Navigation & Filters")

selected_region = st.sidebar.multiselect(
    "Filter by Region",
    options=df["Region"].unique(),
    default=df["Region"].unique()
)

selected_impact = st.sidebar.multiselect(
    "Filter Threat Level",
    options=df["Impact_Level"].unique(),
    default=df["Impact_Level"].unique()
)

filtered_df = df[(df["Region"].isin(selected_region)) & (df["Impact_Level"].isin(selected_impact))]

st.sidebar.divider()
st.sidebar.subheader("Hotspot Focus")
selected_location = st.sidebar.selectbox(
    "Select Specific Conflict",
    options=["Global Overview"] + list(filtered_df["Location"].unique())
)

# --- METRIC CARDS ---
col_m1, col_m2, col_m3, col_m4 = st.columns(4)
col_m1.metric("Active Tracked Hotspots", len(filtered_df))
col_m2.metric("Critical Threat Level", len(filtered_df[filtered_df["Impact_Level"] == "Critical"]))
col_m3.metric("Armed Conflicts / Wars", len(filtered_df[filtered_df["Type"].isin(["Armed Conflict", "Civil War"])]))
col_m4.metric("Regions Monitored", len(filtered_df["Region"].unique()))

st.divider()

# --- TABBED DASHBOARD INTERFACE ---
tab1, tab2, tab3 = st.tabs(["🗺️ Interactive Map & Intelligence", "📊 Threat Analytics", "📖 Strategic Briefs"])

# TAB 1: MAP & LIVE NEWS
with tab1:
    c1, c2 = st.columns([3, 2])
    
    # Set Map Center
    if selected_location != "Global Overview":
        loc_row = df[df["Location"] == selected_location].iloc[0]
        center_lat, center_lon, zoom = loc_row["Latitude"], loc_row["Longitude"], 5
    else:
        center_lat, center_lon, zoom = 20.0, 0.0, 2

    with c1:
        st.subheader("Geospatial Conflict Map")
        m = folium.Map(location=[center_lat, center_lon], zoom_start=zoom, tiles="OpenStreetMap")

        for _, row in filtered_df.iterrows():
            marker_color = "red" if row["Impact_Level"] == "Critical" else "orange" if row["Impact_Level"] == "High" else "blue"
            folium.Marker(
                location=[row["Latitude"], row["Longitude"]],
                popup=f"<b>{row['Location']}</b><br>Type: {row['Type']}<br>Threat: {row['Impact_Level']}",
                tooltip=f"{row['Location']} ({row['Impact_Level']})",
                icon=folium.Icon(color=marker_color, icon="info-sign")
            ).add_to(m)

        st_folium(m, width=700, height=450, key=f"map_{selected_location}")

    with c2:
        st.subheader("📰 Localized Live News Feed")
        search_query = f"{selected_location} conflict" if selected_location != "Global Overview" else "geopolitical conflict OR war"
        
        with st.spinner("Updating live intelligence feed..."):
            news_df, feed_src = fetch_live_news(query=search_query)

        st.caption(f"Source: **{feed_src}** | Target: *`{search_query}`*")
        
        if not news_df.empty:
            st.dataframe(
                news_df,
                column_config={"URL": st.column_config.LinkColumn("Article Link")},
                use_container_width=True,
                height=380
            )
        else:
            st.info("No recent news feed available for this selection.")

# TAB 2: THREAT ANALYTICS
with tab2:
    st.subheader("Regional Conflict Distribution & Threat Severity")
    col_a1, col_a2 = st.columns(2)
    
    with col_a1:
        fig_type = px.pie(
            filtered_df, 
            names="Type", 
            title="Hotspots by Conflict Classification",
            color_discrete_sequence=px.colors.sequential.RdBu
        )
        st.plotly_chart(fig_type, use_container_width=True)

    with col_a2:
        fig_impact = px.bar(
            filtered_df, 
            x="Region", 
            color="Impact_Level", 
            title="Threat Level Severity by Region",
            barmode="stack"
        )
        st.plotly_chart(fig_impact, use_container_width=True)

# TAB 3: STRATEGIC BRIEFS
with tab3:
    st.subheader("Strategic Background & Policy Briefings")
    
    if selected_location != "Global Overview":
        brief_df = df[df["Location"] == selected_location]
    else:
        brief_df = filtered_df

    for _, row in brief_df.iterrows():
        with st.expander(f"📍 **{row['Location']}** — *{row['Type']}* (Threat Level: {row['Impact_Level']})", expanded=True):
            st.write(f"**Region:** {row['Region']} | **Status:** {row['Status']}")
            st.markdown("#### Conflict Background")
            st.write(row['Background'])
            st.markdown("#### Strategic & Global Impact")
            st.write(row['Strategic_Impact'])