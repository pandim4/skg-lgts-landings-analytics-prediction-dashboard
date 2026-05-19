import streamlit as st
import pandas as pd
import sqlalchemy
import plotly.express as px

#Load credentials
import os
from dotenv import load_dotenv
load_dotenv()

#Filters

def make_multiselect_with_select_all(df, column_name, label):
    st.sidebar.markdown(f"**{label}**")

    options = df[column_name].unique()
    if st.sidebar.checkbox(f"Select All {label}", value=True):
        selected_options = st.sidebar.multiselect(f"Select {label}(s)", options=options, default=options)
    else:
        selected_options = st.sidebar.multiselect(f"Select {label}(s)", options=options)
    
    if not selected_options:
        st.warning(f"Please select at least one {label.lower()} to display data.")
        st.stop()
    
    return df[df[column_name].isin(selected_options)]

def make_boolean_widget(df, column_name, label):
    value = st.sidebar.checkbox(label, value=False)

    if value is True:
        return df[df[column_name] == True]
   
    return df


def make_slider_widget(df, column_name, label):
    min_val = df[column_name].min()
    max_val = df[column_name].max()
    selected_range = st.sidebar.slider(label, min_value=float(min_val), max_value=float(max_val), value=(float(min_val), float(max_val)))

    return df[(df[column_name] >= selected_range[0]) & (df[column_name] <= selected_range[1])]


def airline_filter(df):
    # Select Airlines
    df = make_multiselect_with_select_all(df, 'airline', 'Airlines')

    return df


def runway_filter(df):

    # Select Runway Configurations
    df = make_multiselect_with_select_all(df, 'runway_config', 'Runway Configurations')

    #Select Actual Runways
    df = make_multiselect_with_select_all(df, 'runway', 'Actual Runways')

    return df

def wind_filter(df):

    # Wind direction categories
    df = make_multiselect_with_select_all(df, 'wind_direction_category', 'Wind Direction Categories')

    df = make_slider_widget(df, 'wind_dir', 'Wind Direction Range')

    # Wind speed categories
    df = make_multiselect_with_select_all(df, 'wind_speed_category', 'Wind Speed Categories')

    df = make_slider_widget(df, 'wind_speed', 'Wind Speed Range')

    #Wind types
    st.sidebar.markdown("**Wind Types**")
    df = make_boolean_widget(df, 'is_wind_gusty', 'Gusty Wind')
    df = make_boolean_widget(df, 'is_wind_vardaris', 'Vardaris Wind')
    df = make_boolean_widget(df, 'is_wind_sea_breeze', 'Sea Breeze Wind')

    return df


def time_filter(df):

    # Select Time of Day
    df = make_multiselect_with_select_all(df, 'day_period', 'Time of Day')

    # Select Season
    df = make_multiselect_with_select_all(df, 'season', 'Season')

    #Traffic cases
    st.sidebar.markdown("**Traffic**")

    #Hightraffic
    df = make_boolean_widget(df, 'is_high_traffic', 'High Traffic')

    #Nightfall
    df = make_boolean_widget(df, 'is_night', 'Nightfall')

    #Holiday
    df = make_boolean_widget(df, 'is_holiday', 'Holiday')

    return df

def weather_filter(df):

    #Visibility
    df = make_multiselect_with_select_all(df, 'visibility_category', 'Visibility Categories')

    #Weather
    df = make_multiselect_with_select_all(df, 'weather_intensity', 'Weather Intensities')
    df = make_multiselect_with_select_all(df, 'weather_category', 'Weather Categories')

    #Clouds
    df = make_multiselect_with_select_all(df, 'ceiling_category', 'Approach Method Categories')
    df = make_multiselect_with_select_all(df, 'clouds_layers', 'Clouds Layers')
    #df = make_slider_widget(df, 'min_clouds_height', 'Minimum Cloud Height')
    df = make_boolean_widget(df, 'is_ceiling', 'Ceiling Clouds')
    df = make_boolean_widget(df, 'is_convective', 'Convective Clouds')

    #Temperature
    df = make_multiselect_with_select_all(df, 'temperature_category', 'Temperature Categories')
    df = make_slider_widget(df, 'temperature', 'Temperature Range')

    #Pressure
    df = make_multiselect_with_select_all(df, 'pressure_category', 'Pressure Categories')

    return df



def filters(df):


    st.sidebar.header("Filters")
    # Airline filters
    df = airline_filter(df)
    # Runway filters    
    df = runway_filter(df)
    # Wind filters    
    df = wind_filter(df)
    # Time filters    
    df = time_filter(df)
    # Weather filters    
    df = weather_filter(df)
    
    # Wtc categories
    df = make_multiselect_with_select_all(df, 'wtc', 'WTC Categories')

    # Engine number categories
    #df = make_multiselect_with_select_all(df, 'engine', 'Engine Number Categories')

    return df

    #Set up

def setup_page(category=None,page_title=None):
    title = f"""SKG Dashboard - {category}""" if category else """SKG Dashboard"""
    st.set_page_config(page_title=title, page_icon="✈️", layout="wide")
    st.title(page_title + " at SKG/LGTS Airport" if page_title else """✈️ SKG/LGTS Airport Landings Dashboard""")