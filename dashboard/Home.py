import os
from dotenv import load_dotenv
import streamlit as st
import pandas as pd
import sqlalchemy
import plotly.express as px
from functions import filters,setup_page
from config import runway_colors, runway_order

load_dotenv()
engine = sqlalchemy.create_engine(os.getenv('DB_URL'))

@st.cache_data
def get_processed_data():
    df = pd.read_sql("SELECT * FROM final_features", engine)

    geo_df = pd.read_sql("SELECT date,callsign,latitude,longitude,groundspeed,altitude,vertical_rate FROM final_features_extended", engine)

    return df, geo_df

setup_page()
st.subheader("By Panagiotis Dimopoulos ics23035")

df, geo_df = get_processed_data()
df = filters(df)

match_keys = df[['date', 'callsign']]
geo_df = geo_df.merge(match_keys, on=['date', 'callsign'], how='inner')

# 1. Metrics Row
m = st.container()
m.metric("Total Landings", f"{len(df):,}")

m1, m2, m3, m4 = st.columns(4)

m1.metric("Primary Runway", df['runway_config'].mode()[0])
m2.metric("Avg Wind Speed", f"{df['wind_speed'].mean():.1f} kt")
m3.metric("Main Wind Direction", df['wind_direction_category'].mode()[0])
m4.metric("Primary Airline", df['airline'].mode()[0])


st.divider()

# 2. Visualizations Row
col_left, col_right = st.columns(2)

with col_left:
    df['runway_config'] = df['runway_config'].astype(str).str.strip()
    st.subheader("Runway Configuration In-Use")
    fig_runway = px.pie(
        df, 
        names='runway_config', 
        hole=0.4,
        color='runway_config', 
        color_discrete_map=runway_colors, 
        category_orders= runway_order
    )
    st.plotly_chart(fig_runway, use_container_width=True)

with col_right:
    st.subheader("Traffic by Hour")
    df['hour_gr'] = df['hour'].dt.tz_convert('Europe/Athens').dt.hour
    hourly_traffic = df.groupby('hour_gr').size().reset_index(name='counts')

    fig_hour = px.bar(hourly_traffic, 
                    x='hour_gr', 
                    y='counts', 
                    title="Distribution of Landings per Hour (24h Profile)",
                    color_discrete_sequence=['#1976D2'])

    fig_hour.update_xaxes(tickmode='array', tickvals=list(range(24)), ticktext=[f"{i}h" for i in range(24)])

    fig_hour.update_layout(bargap=0.1, xaxis_title="Hour of Day", yaxis_title="Number of Landings")

    st.plotly_chart(fig_hour, use_container_width=True)

# --- ΕΝΟΤΗΤΑ ΧΑΡΤΗ (ΒΕΛΤΙΩΜΕΝΗ) ---
st.divider()
st.subheader("📍 Interactive Flight Path Radar")

if not geo_df.empty:
    # Sampling if dataset is too large for performance
    limit = 30000
    if len(geo_df) > limit:
        plot_geo_df = geo_df.sample(n=limit, random_state=42)
        st.caption(f"Sampling applied: Showing {limit} random points out of {len(geo_df)} total for performance.")
    else:
        plot_geo_df = geo_df

    # Shape the map with Plotly
    fig_map = px.scatter_mapbox(
        plot_geo_df,
        lat="latitude",
        lon="longitude",
        color="altitude",
        size="groundspeed", 
        size_max=4,                
        opacity=0.4,            
        hover_name="callsign",      
        hover_data={
            "altitude": True, 
            "groundspeed": True, 
            "vertical_rate": True,
            "latitude": False,
            "longitude": False
        },
        color_continuous_scale=px.colors.sequential.Jet, 
        range_color=[-400, 1000],
        mapbox_style="carto-positron",
        zoom=11.5,
        center={"lat": 40.5197, "lon": 22.9709},
        height=700
    )

    #Layout adjustments
    fig_map.update_layout(
        margin={"r":0,"t":0,"l":0,"b":0},
        coloraxis_colorbar=dict(title="Altitude (ft)")
    )

    st.plotly_chart(fig_map, use_container_width=True)

else:
    st.warning("⚠️ No geospatial data available to display the flight paths.")  

    # Χρήση expander για να παραμένει καθαρό το dashboard
with st.expander("Click to view Raw Data"):
    st.dataframe(df) # Display the entire dataframe interactively
    st.dataframe(geo_df) # Display the entire geospatial dataframe interactively