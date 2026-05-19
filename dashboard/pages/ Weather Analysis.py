import os
import streamlit as st
import pandas as pd
import sqlalchemy
import plotly.express as px

from dotenv import load_dotenv
from functions import filters,setup_page
from config import runway_order, wind_direction_order, weather_order, visibility_order, all_categories_order
from config import runway_colors, wind_colors, visibility_colors

load_dotenv()
engine = sqlalchemy.create_engine(os.getenv('DB_URL'))

@st.cache_data
def get_processed_data():
    df = pd.read_sql("SELECT * FROM final_features", engine)

    geo_df = pd.read_sql("SELECT timestamp,date,callsign,latitude,longitude,groundspeed,altitude,vertical_rate,geoaltitude FROM final_features_extended", engine)

    return df, geo_df

setup_page(category="Weather", page_title="🌤️ Weather Analysis")

df, geo_df = get_processed_data()

df = filters(df)

col_left, col_right = st.columns(2)

df['runway_config'] = df['runway_config'].astype(str).str.strip()

m = st.container()
m_wind = st.container()
m_visibility = st.container()
m_weather = st.container()

m.metric(label="Total Landings", value=f"{len(df)}")

st.divider()

with m_wind:

    st.subheader("Wind Conditions Overview")

    mw1, mw2, mw3, mw4 = st.columns(4)
    mw1.metric(label="Most Common Wind Direction", value=f"{df['wind_direction_category'].value_counts().idxmax()}",delta=f"{(df['wind_direction_category'].value_counts().max())} landings")
    mw2.metric(label="Average Wind Speed", value=f"{df['wind_speed'].mean():.1f} kts")
    mw3.metric(label="Landings with Vardaris", value=f"{df['is_wind_vardaris'].sum()}",delta=f"{(df['is_wind_vardaris'].sum())/len(df)*100:.1f}%")
    mw4.metric(label="Landings with Sea Breeze", value=f"{df['is_wind_sea_breeze'].sum()}",delta=f"{(df['is_wind_sea_breeze'].sum())/len(df)*100:.1f}%")

    st.divider()

with m_visibility:

    st.subheader("Visibility Conditions Overview")

    mv1, mv2, mv3, mv4,mv5 = st.columns(5)
    mv1.metric(label="Most Common Visibility Category", value=f"{df['visibility_category'].value_counts().idxmax()}",delta=f"{(df['visibility_category'].value_counts().max())} landings")
    mv2.metric(label="Average Visibility", value=f"{df['visibility'].mean():.1f} m")
    mv3.metric(label="Landings with High Visibility", value=f"{df[df['visibility_category'] == 'High'].shape[0]}",delta=f"{(df[df['visibility_category'] == 'High'].shape[0])/len(df)*100:.1f}%")
    mv4.metric(label="Landings with Low Visibility", value=f"{df[df['visibility_category'] == 'Low'].shape[0]}",delta=f"{(df[df['visibility_category'] == 'Low'].shape[0])/len(df)*100:.1f}%")
    mv5.metric(label="Landings with Critical Visibility", value=f"{df[df['visibility_category'] == 'Critical'].shape[0]}",delta=f"{(df[df['visibility_category'] == 'Critical'].shape[0])/len(df)*100:.2f}%")

    st.divider()


with m_weather:

    st.subheader("Weather Conditions Overview")

    mwe1, mwe2,mwe3,mwe4,mwe5 = st.columns(5)
    mwe1.metric(label="Most Common Weather Condition", value=f"{df['weather_category'].value_counts().idxmax()}",delta=f"{(df['weather_category'].value_counts().max())} landings")
    mwe2.metric(label="Average Temperature", value=f"{df['temperature'].mean():.1f} °C")
    mwe3.metric(label="Landings with Clear Weather", value=f"{df[df['weather_category'] == 'Clear'].shape[0]}",delta=f"{(df[df['weather_category'] == 'Clear'].shape[0])/len(df)*100:.1f}%")
    mwe4.metric(label="Landings with Thunderstorm", value=f"{df[df['weather_category'] == 'Thunderstorm'].shape[0]}",delta=f"{(df[df['weather_category'] == 'Thunderstorm'].shape[0])/len(df)*100:.1f}%")
    mwe5.metric(label="Landings with Fog", value=f"{df[df['weather_category'] == 'Fog'].shape[0]}",delta=f"{(df[df['weather_category'] == 'Fog'].shape[0])/len(df)*100:.1f}%")


#m5.metric(label="Runway used most under Vardaris Conditions", value=f"{df[df['is_wind_vardaris'] == True]['runway_config'].value_counts().idxmax()}",delta=f"{(df[df['is_wind_vardaris'] == True]['runway_config'].value_counts().max())} landings")
#m6.metric(label="Runway used most under Sea Breeze Conditions", value=f"{df[df['is_wind_sea_breeze'] == True]['runway_config'].value_counts().idxmax()}",delta=f"{(df[df['is_wind_sea_breeze'] == True]['runway_config'].value_counts().max())} landings")
#m3.metric(label="Runway used most under Foggy Conditions", value=f"{df[df['is_foggy'] == True]['runway_config'].value_counts().idxmax()}",delta=f"{(df[df['is_foggy'] == True]['runway_config'].value_counts().max())} landings")


st.subheader("Runway Configuration Selection based on Weather Status")

def runway_selection_by_weather_status(weather_col, weather_label,category_order,df=df):
    fig = px.histogram(
        df, 
        x=weather_col, 
        color="runway_config",
        color_discrete_map=runway_colors,
        category_orders=category_order,
        barmode="group",
    )

    fig.update_layout(
        xaxis_title=weather_label,
        yaxis_title="Number of Landings", 
        legend_title="Runway Configuration",
        title=f"Runway Configuration Selection by {weather_label}")

    st.plotly_chart(fig, use_container_width=True)



#Graph: Runway Selection by Wind Direction Category
runway_selection_by_weather_status("wind_direction_category", "Wind Direction Category",all_categories_order,df)
runway_selection_by_weather_status("weather_category", "Weather Condition excluding Clear",all_categories_order,df[df['weather_category'] != 'Clear'])
runway_selection_by_weather_status("visibility_category", "Visibility Category excluding High",all_categories_order,df[df['visibility_category'] != 'High'])

st.divider()



#Wind Section
st.subheader("Wind Conditions Analysis")

#Graph: Wind Rose


col1, col2 = st.columns(2)

#Grouping the wind direction into 20-degree bins
df['wind_dir_binned'] = (df['wind_dir'] // 20) * 20 

#Rose data: count of landings for each wind direction bin and wind speed category
rose_data = df.groupby(['wind_dir_binned', 'wind_speed_category', 'runway_config']).size().reset_index(name='count')

def rose_plot_by_category(category_col, category_label, color_discrete_sequence=None,color_discrete_map=None):
    fig_rose = px.bar_polar(
        rose_data, 
        r="count",                      # Η ακτίνα δείχνει τη συχνότητα (πόσες πτήσεις)
        theta="wind_dir_binned",        # Η γωνία δείχνει την κατεύθυνση σε μοίρες
        color=category_col, 
        color_discrete_sequence=color_discrete_sequence,
        color_discrete_map=color_discrete_map,
        template="plotly_dark",
        direction="clockwise",
        start_angle=90,                 # Ο Βορράς στην κορυφή
        barmode="stack",
        title=f"Wind Rose: Landing Frequency by Direction & {category_label}"
    )   


    fig_rose.update_layout(
        polar=dict(
            radialaxis=dict(showticklabels=False, ticks=''),
            angularaxis=dict(tickmode='array', tickvals=[0,45,90,135,180,225,270,315], ticktext=['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'])
        ),  
        legend=dict(title=category_label)
    )


    st.plotly_chart(fig_rose, use_container_width=True)

with col1:

    rose_plot_by_category("wind_speed_category", "Wind Speed Category", color_discrete_sequence=px.colors.sequential.Plasma_r)

with col2:

    rose_plot_by_category("runway_config", "Runway Configuration", color_discrete_map=runway_colors)


def pie_runway_distribution(df, condition_col, condition_label):
    fig_runway = px.pie(
        df[df[condition_col] == True], 
        names='runway_config', 
        hole=0.4,
        color='runway_config', 
        color_discrete_map=runway_colors, 
        category_orders= runway_order,
        title=f"Runway Configuration Distribution under {condition_label} Conditions"

    )

    fig_runway.update_layout(legend_title_text='Runway Configuration')

    st.plotly_chart(fig_runway, use_container_width=True)

df['runway_config'] = df['runway_config'].astype(str).str.strip()

with col1:
    pie_runway_distribution(df, 'is_wind_vardaris', 'Vardaris')

with col2:
    pie_runway_distribution(df, 'is_wind_sea_breeze', 'Sea Breeze')

wind_df = df
match_keys = wind_df[['date', 'callsign', 'wind_speed','wind_dir', 'wind_direction_category', 'wind_speed_category', 'runway_config']]
wind_geo_df = geo_df.merge(match_keys, on=['date', 'callsign'], how='inner')

def scatter_wind_speed_vs_geodata(wind_geo_df,geodata_col, geodata_label,color_col, color_label):
    fig = px.scatter(
        wind_geo_df[wind_geo_df['altitude'] >0],
        x="wind_speed",
        y=geodata_col,
        color=color_col,
        color_discrete_map=runway_colors if color_col == "runway_config" else None,
        trendline="ols",
        opacity=0.3,
        title=f"Wind Speed vs {geodata_label} Colored by {color_label}",
        labels={'wind_speed': 'Wind Speed (kts)', geodata_col: geodata_label, color_col: color_label},
        template="plotly_dark"
    )
    st.plotly_chart(fig, use_container_width=True)


scatter_wind_speed_vs_geodata(wind_geo_df, "groundspeed", "Ground Speed", "runway_config", "Runway Configuration")
#scatter_wind_speed_vs_geodata(wind_geo_df, "geoaltitude", "Geoaltitude", "wind_speed_category", "Wind Speed Category")
#scatter_wind_speed_vs_geodata(wind_geo_df, "geoaltitude", "Geoaltitude", "wind_direction_category", "Wind Direction Category")
#scatter_wind_speed_vs_geodata(wind_geo_df, "geoaltitude", "Geoaltitude", "weather_category", "Weather Category")
#scatter_wind_speed_vs_geodata(wind_geo_df, "geoaltitude", "Geoaltitude", "visibility_category", "Visibility Category")

#scatter_wind_speed_vs_geodata(wind_geo_df, "groundspeed", "Ground Speed", "altitude", "Altitude Category")






#fig_vardaris_profile = px.line(
    #y="altitude",
    #color="callsign",
   # title="Προφίλ Καθόδου υπό συνθήκες Βαρδάρη",
   # template="plotly_dark"
#)
#fig_vardaris_profile.update_yaxes(range=[0, 1200]) # Εστίαση στα τελευταία 5000 πόδια
#st.plotly_chart(fig_vardaris_profile, use_container_width=True)









sample_size = 200

adverse_sample = df[df['weather_category'] != 'Clear'].sample(sample_size, random_state=42)
clear_sample = df[df['weather_category'] == 'Clear'].sample(sample_size, random_state=42)
combined_sample = pd.concat([adverse_sample, clear_sample])
match_keys = combined_sample[['date', 'callsign', 'weather_category']]
combined_sample_geo = geo_df.merge(match_keys, on=['date', 'callsign'], how='inner')


vardaris_sample = df[df['is_wind_vardaris'] == True].sample(sample_size, random_state=40)
seabreeze_sample = df[df['is_wind_sea_breeze'] == True].sample(sample_size, random_state=40)
clear_sample_2 = df[(df['is_wind_sea_breeze'] != True) & (df['is_wind_vardaris'] != True)].sample(sample_size, random_state=42)
vardaris_sample['wind_type'] = 'Vardaris'
seabreeze_sample['wind_type'] = 'Sea Breeze'
clear_sample_2['wind_type'] = 'Other'
combined_sample_2 = pd.concat([vardaris_sample, seabreeze_sample, clear_sample_2])
match_keys_2 = combined_sample_2[['date', 'callsign', 'wind_type']]
combined_sample_geo_2 = geo_df.merge(match_keys_2, on=['date', 'callsign'], how='inner')

critical_visibility_sample = df[df['visibility_category'] == 'Critical'].sample(sample_size, random_state=42) if df[df['visibility_category'] == 'Critical'].shape[0] >= sample_size else df[df['visibility_category'] == 'Critical']
low_visibility_sample = df[df['visibility_category'] == 'Low'].sample(sample_size, random_state=42) if df[df['visibility_category'] == 'Low'].shape[0] >= sample_size else df[df['visibility_category'] == 'Low']
medium_visibility_sample = df[df['visibility_category'] == 'Medium'].sample(sample_size, random_state=42) if df[df['visibility_category'] == 'Medium'].shape[0] >= sample_size else df[df['visibility_category'] == 'Medium']
high_visibility_sample = df[df['visibility_category'] == 'High'].sample(sample_size, random_state=42) if df[df['visibility_category'] == 'High'].shape[0] >= sample_size else df[df['visibility_category'] == 'High']
combined_sample_3 = pd.concat([critical_visibility_sample, low_visibility_sample, medium_visibility_sample, high_visibility_sample])
match_keys_3 = combined_sample_3[['date', 'callsign', 'visibility_category']]
combined_sample_geo_3 = geo_df.merge(match_keys_3, on=['date', 'callsign'], how='inner')

def threeD_landing_profiles_by_weather_status(combined_sample, weather_col, weather_label,colors=None):

    unique_callsigns = combined_sample['callsign'].unique()
    unique_callsigns = unique_callsigns[:15]  # Περιορισμός σε 100 callsigns για καλύτερη απόδοση
    combined_sample = combined_sample[combined_sample['callsign'].isin(unique_callsigns)]
    combined_sample = combined_sample.sort_values(['callsign', 'date'])

    combined_sample['flight_id'] = combined_sample['callsign'] + "_" + combined_sample['date'].astype(str)


    fig_3d = px.line_3d(
        combined_sample[combined_sample['vertical_rate'] != 0], 
        x='longitude', 
        y='latitude', 
        z='geoaltitude',
        line_group='flight_id',
        color=weather_col,
        color_discrete_map = colors,
        title=f"3D Landing Profiles by {weather_label}"
    )

    fig_3d.update_layout(
        legend_title=weather_label,
        scene=dict(
            xaxis_title='Longitude',
            yaxis_title='Latitude',
            zaxis_title='Altitude (ft)',
            zaxis=dict(range=[0, 1200])
        )
    )
    st.plotly_chart(fig_3d)


st.subheader("3D Landing Profiles by Different Weather Conditions")

#Graph: 3D Landing Profiles by Weather Condition
threeD_landing_profiles_by_weather_status(combined_sample_geo, "weather_category", "Weather Condition")
threeD_landing_profiles_by_weather_status(combined_sample_geo_2, "wind_type", "Wind Type", colors=wind_colors)
threeD_landing_profiles_by_weather_status(combined_sample_geo_3, "visibility_category", "Visibility Category", colors=visibility_colors)


def box_plot_groundspeed_by_weather_status(combined_sample, weather_col, weather_label, colors=None):
    fig_box = px.box(
        combined_sample, 
        x=weather_col, 
        y="groundspeed", 
        color=weather_col,
        color_discrete_map=colors,
        points=False,
        title=f"Ground Speed Variability by {weather_label}"
    )

    fig_box.update_layout(
        xaxis_title=weather_label,
        yaxis_title="Ground Speed (kts)", 
        legend_title=weather_label
    )
    st.plotly_chart(fig_box)



st.subheader("Ground Speed Variability by Different Weather Conditions")

#Graph: Box Plot of Ground Speed by Weather Condition
box_plot_groundspeed_by_weather_status(combined_sample_geo, "weather_category", "Weather Condition")
st.write("Average Ground Speed by Weather Condition:")
st.write(combined_sample_geo.groupby("weather_category")["groundspeed"].mean())

box_plot_groundspeed_by_weather_status(combined_sample_geo_2, "wind_type", "Wind Type", colors=wind_colors)
st.write("Average Ground Speed by Wind Type:")
st.write(combined_sample_geo_2.groupby("wind_type")["groundspeed"].mean())

box_plot_groundspeed_by_weather_status(combined_sample_geo_3, "visibility_category", "Visibility Category", colors=visibility_colors)
st.write("Average Ground Speed by Visibility Category:")
st.write(combined_sample_geo_3.groupby("visibility_category")["groundspeed"].mean())
