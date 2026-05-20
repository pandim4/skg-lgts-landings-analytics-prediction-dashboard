# This module contains functions for feature engineering, METAR parsing, and machine learning model creation and prediction.
import numpy as np
import pandas as pd
import requests
from datetime import datetime, timezone
import streamlit as st
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv

from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier

from astral import LocationInfo
from astral.sun import sun
import holidays


#----- Features Creation -----#

### Time features ###

gr_holidays = holidays.Greece(years=[2024])
city = LocationInfo(name="Thessaloniki", region="Greece", timezone="Europe/Athens", latitude=40.6401, longitude=22.9444)

def is_night(fg):
    """Evaluates if an astronomical solar night phase is active for a given timestamp."""
    s = sun(city.observer, date=fg['timestamp'].date(), tzinfo=city.timezone)
    local_tz = fg['timestamp'].tz_convert('Europe/Athens')
    
    return (local_tz < s['sunrise']) or (local_tz > s['sunset'])

def calendar_season(month):
    """Maps numeric month representations into corresponding seasonal categories."""
    winter = set([12, 1, 2])
    spring = set([3, 4, 5])
    summer = set([6, 7, 8])
    autumn = set([9, 10, 11])
    
    if month in winter:
        return 'Winter'
    elif month in spring:
        return 'Spring'
    elif month in summer:
        return 'Summer'
    elif month in autumn:
        return 'Autumn'

def day_period(h):
    """Maps specific localized hour ranges into broad, analytical time-of-day categories."""
    local_hour = h.tz_convert('Europe/Athens').hour
    
    # Mapping to periods
    if 4 <= local_hour < 8:
        return "Early Morning"
    elif 8 <= local_hour < 12:
        return "Morning"
    elif 12 <= local_hour < 17:
        return "Afternoon"
    elif 17 <= local_hour < 21:
        return "Evening"
    else:
        return "Night"

def apply_time_features(landings_df):
    """
    Extracts time features from timestamps, maps seasonal fields, computes night states,
    and flags national holiday observations.

    Args:
        landings_df (pd.DataFrame): Core approach observations log.

    Returns:
        pd.DataFrame: Dataframe populated with structured time attributes.
    """
    current_year = pd.Timestamp.now().year
 
    landings_df['monthday'] = landings_df['timestamp'].dt.day
    landings_df['weekday'] = landings_df['timestamp'].dt.dayofweek
    landings_df['day_period'] = landings_df['hour'].apply(day_period)
    landings_df['month'] = landings_df['timestamp'].dt.month
    landings_df['season'] = landings_df['month'].apply(calendar_season)
    landings_df['calendar'] = np.where(
        (landings_df['timestamp'] < pd.Timestamp(current_year, 3, 31, tz='UTC')) | 
        (landings_df['timestamp'] > pd.Timestamp(current_year, 10, 27, tz='UTC')), 
        'Winter', 'Summer'
    )
    landings_df['is_night'] = landings_df.apply(is_night, axis=1)
    landings_df['is_holiday'] = landings_df['timestamp'].dt.date.isin(gr_holidays)

    return landings_df


### Weather features ###

### Wind Section ###
def calculate_winds(df):
    """
    Calculates advanced meteorological wind vectors, identifies gust parameters,
    determines specific local wind phenomena (Vardaris, Sea Breeze), labels direction
    quadrants, and calculates runway headwinds/crosswinds.

    Args:
        df (pd.DataFrame): Dataframe containing base weather reports.

    Returns:
        None
    """
    # Wind Gusts Features
    df['wind_gusts'] = df['wind_gusts'].fillna(df['wind_speed'])
    df['gust_factor'] = df['wind_gusts'] / df['wind_speed'].replace(0, np.nan)
    df['gust_delta'] = df['wind_gusts'] - df['wind_speed']
    df['is_wind_gusty'] = (df['gust_factor'] > 1).astype(bool)

    # Varying Wind Features
    df['is_wind_vrb'] = (df['wind_dir'] == -1).astype(bool)
    df['varying_spread'] = (df['varying_wind_to'] - df['varying_wind_from']) % 360
    df['varying_spread'] = df['varying_spread'].fillna(0)

    # Vardaris Feature
    vardaris_direction = 340
    df['is_wind_vardaris'] = (abs((df['wind_dir'] - vardaris_direction + 180) % 360 - 180) <= 30) & ((df['wind_speed'] >= 15) | (df['gust_factor'] > 1))

    # Sea Breeze Feature
    sea_breeze_direction = 180
    df['is_wind_sea_breeze'] = (abs((df['wind_dir'] - sea_breeze_direction + 180) % 360 - 180) <= 30) & (df['wind_speed'].between(3, 15))

    # Wind Speed Category
    def wind_speed_category(speed):
        if speed < 5: return "Calm"
        elif speed < 15: return "Light"
        elif speed < 25: return "Moderate"
        elif speed < 35: return "Strong"
        else: return "Very Strong"
    
    df['wind_speed_category'] = df['wind_speed'].apply(wind_speed_category)

    # Wind Direction Category
    def wind_direction_category(direction):
        if direction == -1: return "Variable"
        direction = direction % 360
        if 337.5 <= direction or direction < 22.5: return "North"
        elif 22.5 <= direction < 67.5: return "Northeast"
        elif 67.5 <= direction < 112.5: return "East"
        elif 112.5 <= direction < 157.5: return "Southeast"
        elif 157.5 <= direction < 202.5: return "South"
        elif 202.5 <= direction < 247.5: return "Southwest"
        elif 247.5 <= direction < 292.5: return "West"
        elif 292.5 <= direction < 337.5: return "Northwest"
    
    df['wind_direction_category'] = df['wind_dir'].apply(wind_direction_category)

    # Wind per runway.
    runways = [104, 284, 166, 346]
    speed = df['wind_speed'].copy()
    direction = df['wind_dir'].copy()
    speed[df['is_wind_vrb']] = 0
    direction[df['is_wind_vrb']] = 0
   
    for runway in runways:
        radians = np.radians(direction - runway)
        df[f'headwind_{runway//10}'] = speed * np.cos(radians)
        df[f'crosswind_{runway//10}'] = speed * np.sin(radians)

    
### Weather phenomena section ###
def calculate_weather_phenomena(df):
    """
    Standardizes categorical representations of weather element intensity 
    and groups composite atmospheric descriptions into primary analytical bins.

    Args:
        df (pd.DataFrame): Weather observation dataframe dataset.

    Returns:
        None
    """
    intensity_map = {'-1': 'Light', '2': 'Heavy'}
    df['weather_intensity'] = df['weather_intensity'].map(intensity_map)
    mask = (df['weather_intensity'].isna()) & (df[['weather_descriptor', 'weather_precipitation', 'weather_obscuration']]).notna().any(axis=1)
    df.loc[mask, 'weather_intensity'] = 'Moderate'
    df['weather_intensity'] = df['weather_intensity'].fillna('No')

    weather_category = [
        df['weather_descriptor'] == 'TS',                                     
        df['weather_obscuration'] == 'FG',                                   
        (df['weather_precipitation'] == 'RA') | (df['weather_descriptor'] == 'SH'), 
        df['weather_precipitation'] == 'DZ',                                  
        df['weather_obscuration'] == 'BR',                                   
        df['weather_precipitation'].isna() & df['weather_descriptor'].isna() & df['weather_obscuration'].isna() # Clear
    ]

    categories = ['Thunderstorm', 'Fog', 'Rain', 'Drizzle', 'Mist', 'Clear']
    df['weather_category'] = np.select(weather_category, categories, default='Other')

def visibility_category(visibility):
    """Maps continuous horizontal visibility metrics into aviation-focused ordinal scale strings."""
    if visibility < 300: return "Critical"
    elif visibility <= 800: return "Low"
    elif visibility < 5000: return "Medium"
    else: return "High"

def temperature_category(temperature):
    """Categorizes standard outdoor ambient temperatures into human/operational bands."""
    if temperature < 0: return "Very Cold"
    elif temperature < 10: return "Cold"
    elif temperature < 20: return "Mild"
    elif temperature < 30: return "Warm"
    else: return "Hot"

def pressure_category(pressure):
    """Categorizes barometric pressure measurements into standard low/high segments."""
    if pressure < 990: return "Very Low"
    elif pressure < 1005: return "Low"
    elif pressure < 1020: return "Normal"
    elif pressure < 1030: return "High"
    else: return "Very High"

def ceiling_category(ceil, visibility=None):
    """
    Determines standard aviation flight rule classifications (LIFR, IFR, MVFR, VFR) 
    based on combinations of cloud ceilings and horizontal visibility metrics.
    """
    if pd.isna(ceil): return "VFR"
        
    if ceil < 500 or visibility < 1500: return 'LIFR'
    elif ceil < 1000 or visibility < 5000: return 'IFR'
    elif ceil <= 3000 or visibility < 8000: return 'MVFR'
    else: return 'VFR'

def calculate_clouds(df):
    """
    Aggregates stratified multi-layer cloud variables to derive structural indicators,
    detects ceiling thresholds from coverage states, and flags presence of convective cloud types.

    Args:
        df (pd.DataFrame): Weather observation table structure.

    Returns:
        pd.DataFrame: The updated dataframe containing calculated cloud features.
    """
    height_columns = ['cloud1_height', 'cloud2_height', 'cloud3_height']
    amount_columns = ['cloud1_amount', 'cloud2_amount', 'cloud3_amount']
    formation_columns = ['cloud1_formation', 'cloud2_formation', 'cloud3_formation']
    
    df['min_clouds_height'] = df[height_columns].min(axis=1)
    df['clouds_layers'] = df[height_columns].count(axis=1)

    ceiling_values = ['BKN', 'OVC']
    temp_heights = df[height_columns].where(df[amount_columns].isin(ceiling_values).values)
    df['ceiling_height'] = temp_heights.min(axis=1)
    df['is_ceiling'] = df['ceiling_height'].notna()
    df['ceiling_category'] = df[['ceiling_height', 'visibility']].apply(lambda x: ceiling_category(x['ceiling_height'], x['visibility']), axis=1)

    convective_values = ['CB', 'TCU']
    temp_heights = df[height_columns].where(df[formation_columns].isin(convective_values).values)
    df['convective_height'] = temp_heights.min(axis=1)
    df['is_convective'] = df['convective_height'].notna()
  
    return df

def calculate_weather_features(weather_df):
    """
    Consolidates sub-routine processing structures to calculate the full spectrum 
    of structural weather features and formats column sorting orders.

    Args:
        weather_df (pd.DataFrame): Parsed metrics weather log inputs.

    Returns:
        pd.DataFrame: Sorted dataframe structured for database integration.
    """
    calculate_winds(weather_df)
    calculate_weather_phenomena(weather_df)
    calculate_clouds(weather_df)

    weather_df['visibility_category'] = weather_df['visibility'].apply(visibility_category)
    weather_df['temperature_category'] = weather_df['temperature'].apply(temperature_category)
    weather_df['pressure_category'] = weather_df['pressure'].apply(pressure_category)

    # Drop intermediate columns
    weather_df = weather_df.drop(columns=[
        'wind_gusts', 'weather_descriptor', 'weather_precipitation', 'weather_obscuration',
        'cloud1_height', 'cloud2_height', 'cloud3_height', 'cloud1_amount', 'cloud2_amount', 
        'cloud3_amount', 'cloud1_formation', 'cloud2_formation', 'cloud3_formation'
    ])

    # Final order
    timestamp = ['timestamp']
    wind = ['wind_dir', 'wind_direction_category', 'wind_speed', 'wind_speed_category', 'is_wind_vrb', 'varying_spread', 'varying_wind_from', 'varying_wind_to', 'is_wind_gusty', 'gust_factor', 'gust_delta', 'is_wind_vardaris', 'is_wind_sea_breeze', 'headwind_10', 'crosswind_10', 'headwind_28', 'crosswind_28', 'headwind_16', 'crosswind_16', 'headwind_34', 'crosswind_34']
    weather_phenomena = ['weather_intensity', 'weather_category']
    other = ['temperature', 'temperature_category', 'dew_point', 'visibility', 'visibility_category', 'pressure', 'pressure_category']
    clouds = ['min_clouds_height', 'clouds_layers', 'is_ceiling', 'ceiling_height', 'ceiling_category', 'is_convective', 'convective_height']
    
    columns_order = timestamp + wind + weather_phenomena + other + clouds
    weather_df = weather_df.reindex(columns=columns_order)

    return weather_df


#---- METAR Parsing Section ----#

def metar_parser(df):
    """
    Parses structural weather information from a METAR string in a single-row DataFrame.
    
    Extracts individual weather elements such as wind, visibility, runway states, 
    clouds, temperature, and pressure using regular expressions.

    Args:
        df (pd.DataFrame): A DataFrame containing a single row with a 'metar' column and a 'date' column.

    Returns:
        pd.DataFrame: A single-row DataFrame containing all the parsed and mapped METAR features.
    """
    import re

    datacoles = {
        "name": ["time", "wind", "varyingwind", "visibility", "lvisibility", "rvisibility", "weather", "clouds", "temperature", "pressure", "cavok", "trend"],
        "re": [
            r".*Z$", r"([0-9]{3}|VRB)([0-9]{2})(G([0-9]{2}))?KT$", r"([0-9]+)V([0-9]+)$", r"[0-9]{4}$", r"([0-9]{4})((N|S|E|W)+)$",
            r"R([0-9]{2})/([0-9]{4})$", r"(\+|\-|VC)?((RE|MI|PR|BC|DR|BL|SH|TS|FZ)*)((DZ|RA|SN|SG|GS|GR|PL|IC|UP)*)((FG|BR|HZ|VA|DU|FU|SA|PY)*)((SQ|PO|DS|SS|FC)*)$",
            r"(FEW|SCT|BKN|OVC)([0-9]{3})(TCU|CB)?$", r"(M)?([0-9]+)/(M)?([0-9]+)$", r"Q([0-9]{4})$", r"CAVOK", r"(NOSIG|TEMPO|BECMG)"
        ]
    }

    final_datacoles = {
        "name": [
            "wind_dir", "wind_speed", "wind_gusts", "varying_wind_from", "varying_wind_to",
            "visibility", "local_visibility", "local_visibility_dir", "runway1_id", "runway1_visibility", "runway2_id", "runway2_visibility",
            "temperature", "dew_point",
            "weather_intensity", "weather_descriptor", "weather_precipitation", "weather_obscuration", "weather_other",
            "pressure", "cavok_recorded", "trend_status",
            "cloud1_amount", "cloud1_height", "cloud1_formation", "cloud2_amount", "cloud2_height", "cloud2_formation", "cloud3_amount", "cloud3_height", "cloud3_formation",
            "extra_wind_dir", "extra_wind_speed", "extra_wind_gusts", "extra_visibility",
            "extra_weather_intensity", "extra_weather_descriptor", "extra_weather_precipitation", "extra_weather_obscuration", "extra_weather_other",
            "extra_cloud1_amount", "extra_cloud1_height", "extra_cloud1_formation", "extra_cloud2_amount", "extra_cloud2_height", "extra_cloud2_formation"
        ]
    }

    temp_data = {}
    final_data = {}

    for name in final_datacoles["name"]:
        temp_data[name] = {}
        final_data[name] = []
        
    parts = df["metar"].iloc[0].split() 
    data = {} 

    for name in datacoles["name"]:
        data[name] = {"values": [], "positions": []}
     
    for j in range(len(parts)):
        for m in range(len(datacoles["re"])):
            current = re.match(datacoles["re"][m], parts[j])
            if current != None:
                data[datacoles["name"][m]]["values"].append(current)
                data[datacoles["name"][m]]["positions"].append(j)

    for name in final_datacoles["name"]:
        temp_data[name] = None
     
    ## TREND SECTION
    recorded = False
    if data["trend"]["values"] != []:
        trend_data = data["trend"]["values"][0]
        trend_position = data["trend"]["positions"][0]
        recorded = True
    
    temp_data["trend_status"] = 0
    if recorded:
        if trend_data.group() == "BECMG": temp_data["trend_status"] = 1
        if trend_data.group() == "TEMPO": temp_data["trend_status"] = 2

    def is_trendy(name):
        if name != "clouds":
            return (temp_data["trend_status"] != 0 and (len(data[name]["values"]) > 1))
        else:
            return (temp_data["trend_status"] != 0) and (len(data[name]["values"]) > 1) and (max(data[name]["positions"]) > trend_position)
           
    ## CAVOK SECTION
    temp_data["cavok_recorded"] = False
    if data["cavok"]["values"] != []:
        temp_data["cavok_recorded"] = True
        
    ## WIND SECTION
    def default_wind():
        temp_data["wind_dir"] = int(wind_data[0].group(1)) if wind_data[0].group(1) != "VRB" else -1
        temp_data["wind_speed"] = int(wind_data[0].group(2))
        temp_data["wind_gusts"] = int(wind_data[0].group(4)) if wind_data[0].group(3) != None else None

    def trendy_wind():
        default_wind()
        temp_data["extra_wind_dir"] = int(wind_data[1].group(1)) if wind_data[1].group(1) != "VRB" else -1
        temp_data["extra_wind_speed"] = int(wind_data[1].group(2))
        temp_data["extra_wind_gusts"] = int(wind_data[1].group(4)) if wind_data[1].group(3) != None else None

    wind_data = data["wind"]["values"]  
    if is_trendy("wind"): trendy_wind()
    else: default_wind()
        
    ## VARYING WIND SECTION
    recorded = False
    if data["varyingwind"]["values"] != []:
        varyingwind_data = data["varyingwind"]["values"][0]
        recorded = True

    if recorded:
        temp_data["varying_wind_from"] = int(varyingwind_data.group(1))
        temp_data["varying_wind_to"] = int(varyingwind_data.group(2))

    ## VISIBILITY SECTION
    def default_visibility():
        temp_data["visibility"] = int(visibility_data[0].group())

    def trendy_visibility():
        default_visibility()
        temp_data["extra_visibility"] = int(visibility_data[1].group())
  
    recorded = False
    if data["visibility"]["values"] != []:
        recorded = True
        visibility_data = data["visibility"]["values"]
    
    if recorded:
        if is_trendy("visibility"): trendy_visibility()
        else: default_visibility()
    else: 
        if temp_data["cavok_recorded"]:
            temp_data["visibility"] = int(9999)

    ## LOCAL VISIBILITY SECTION
    recorded = False
    if data["lvisibility"]["values"] != []:
        local_visibility_data = data["lvisibility"]["values"][0]
        recorded = True
    
    if recorded:
        temp_data["local_visibility"] = int(local_visibility_data.group(1))
        temp_data["local_visibility_dir"] = local_visibility_data.group(2) 
          
    ## RUNWAY VISIBILITY SECTION
    recorded = False
    if data["rvisibility"]["values"] != []:
        runway_visibility_data = data["rvisibility"]["values"]
        recorded = True
    
    if recorded:
        records = len(runway_visibility_data)  
        temp_data["runway1_id"] = int(runway_visibility_data[0].group(1))
        temp_data["runway1_visibility"] = int(runway_visibility_data[0].group(2))
        temp_data["runway2_id"] = int(runway_visibility_data[1].group(1)) if records > 1 else None
        temp_data["runway2_visibility"] = int(runway_visibility_data[1].group(2)) if records > 1 else None

    ## TEMPERATURE SECTION
    temperature_data = data["temperature"]["values"][0]
    temperature_sign = -1 if temperature_data.group(1) == "M" else 1
    dew_point_sign = -1 if temperature_data.group(3) == "M" else 1       
    temp_data["temperature"] = int(temperature_data.group(2)) * temperature_sign
    temp_data["dew_point"] = int(temperature_data.group(4)) * dew_point_sign

    ## WEATHER SECTION
    def default_weather():
        if weather_data[0].group(1) != None:
            temp_data["weather_intensity"] = 1 if weather_data[0].group(1) == "+" else -1
            if weather_data[0].group(1) == "VC": temp_data["weather_intensity"] = 2
        temp_data["weather_descriptor"] = weather_data[0].group(3)
        temp_data["weather_precipitation"] = weather_data[0].group(5)
        temp_data["weather_obscuration"] = weather_data[0].group(7)
        temp_data["weather_other"] = weather_data[0].group(9)
        
    def trendy_weather():
        default_weather()
        if weather_data[1].group(1) != None:
            temp_data["extra_weather_intensity"] = 1 if weather_data[1].group(1) == "+" else -1
            if weather_data[1].group(1) == "VC": temp_data["extra_weather_intensity"] = 2
        temp_data["extra_weather_descriptor"] = weather_data[1].group(3)
        temp_data["extra_weather_precipitation"] = weather_data[1].group(5)
        temp_data["extra_weather_obscuration"] = weather_data[1].group(7)
        temp_data["extra_weather_other"] = weather_data[1].group(9)
    
    recorded = False
    if data["weather"]["values"] != []:
        recorded = True
        weather_data = data["weather"]["values"]

    if recorded:
        if is_trendy("weather"): trendy_weather()
        else: default_weather()          

    ## PRESSURE SECTION
    recorded = False
    if data["pressure"]["values"] != []:
        pressure_data = data["pressure"]["values"][0]
        recorded = True

    if recorded:
        temp_data["pressure"] = int(pressure_data.group(1))

    ## CLOUDS SECTION
    def default_clouds():
        for k, cloud in enumerate(clouds_data):
            if k < 3:
                temp_data[f"cloud{k+1}_amount"] = cloud.group(1)
                temp_data[f"cloud{k+1}_height"] = int(cloud.group(2)) * 100
                temp_data[f"cloud{k+1}_formation"] = cloud.group(3)

    def trendy_clouds():
        default_clouds()
        for k, cloud in enumerate(clouds_data):
            if k >= 3:
                temp_data[f"extra_cloud{k-2}_amount"] = cloud.group(1)
                temp_data[f"extra_cloud{k-2}_height"] = int(cloud.group(2)) * 100
                temp_data[f"extra_cloud{k-2}_formation"] = cloud.group(3)
        
    recorded = False
    if data["clouds"]["values"] != []:
        clouds_data = data["clouds"]["values"]
        recorded = True

    if recorded:
        if is_trendy("clouds"): trendy_clouds()
        else: default_clouds()

    for name in final_datacoles["name"]:
        final_data[name].append(temp_data[name])
    
    fdf = pd.DataFrame(final_data)
    return fdf


#---- Forecasting & Data Fetching ----#

@st.cache_data(ttl=3600)
def get_metar_forecast_df(lat=40.52, lon=22.97, station="LGTS"):
    """
    Retrieves hourly METAR forecast data from the Open-Meteo API, maps WMO codes 
    to METAR descriptors, and constructs forecast strings.

    Args:
        lat (float): Latitude of the target airport.
        lon (float): Longitude of the target airport.
        station (str): The ICAO code of the airport.

    Returns:
        pd.DataFrame: A dataframe containing forecast timestamps and generated METAR strings.
    """
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": ["temperature_2m", "dew_point_2m", "wind_speed_10m", 
                   "wind_direction_10m", "weather_code", "visibility", 
                   "pressure_msl", "cloud_base", "cloud_cover"],
        "timezone": "UTC"
    }

    data = requests.get(url, params=params).json()
    h = data["hourly"]
    
    # Mapping WMO Weather Codes to METAR descriptors
    wmo_to_metar = {
        0: "", 1: "", 2: "", 3: "",                # Clear/Cloudy
        45: "FG", 48: "FZFG",                      # Fog
        51: "-DZ", 53: "DZ", 55: "+DZ",            # Drizzle
        61: "-RA", 63: "RA", 65: "+RA",            # Rain
        66: "-FZRA", 67: "FZRA",                   # Freezing Rain
        71: "-SN", 73: "SN", 75: "+SN",            # Snow
        80: "-SHRA", 81: "SHRA", 82: "+SHRA",      # Showers
        95: "TS", 96: "TSRA", 99: "+TSRA"          # Thunderstorms
    }

    now_str = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0).strftime("%Y-%m-%dT%H:00")
    try:
        start = h["time"].index(now_str)
    except ValueError:
        start = 0

    target_indices = [start + i for i in range(2, 14, 2)]
    target_indices.append(start + 24)

    rows = []

    for i in target_indices:
        if i >= len(h["time"]): break
            
        time_val = h["time"][i]
        temp = h["temperature_2m"][i]
        dew = h["dew_point_2m"][i]
        w_spd_kt = h["wind_speed_10m"][i] * 0.54
        w_dir = h["wind_direction_10m"][i]
        vis_m = h["visibility"][i]
        qnh_val = h["pressure_msl"][i]
        c_base = h["cloud_base"][i]
        c_cov = h["cloud_cover"][i]
        w_code = h["weather_code"][i]

        # Time and Wind
        ts = datetime.strptime(time_val, "%Y-%m-%dT%H:%M").strftime("%d%H%MZ")
        wind_str = f"{int(w_dir):03d}{int(w_spd_kt):02d}KT"
        
        # Visibility
        vis_str = "9999" if vis_m >= 9999 else f"{int(vis_m):04d}"
        
        # Weather
        weather_str = wmo_to_metar.get(w_code, "")

        # Sky Condition
        if c_base is None or c_cov < 10:
            sky_str = "" 
        else:
            alt = int(c_base * 3.28 / 100)
            pre = "FEW" if c_cov < 25 else "SCT" if c_cov < 50 else "BKN" if c_cov < 85 else "OVC"
            sky_str = f"{pre}{alt:03d}"

        # Construct final string
        components = [station, ts, wind_str, vis_str, weather_str, sky_str, f"{int(temp):02d}/{int(dew):02d}", f"Q{int(qnh_val)}"]
        metar_string = " ".join([c for c in components if c])

        rows.append({
            "time": time_val,
            "metar": metar_string,
        })

    return pd.DataFrame(rows)

@st.cache_data(ttl=900)
def get_metar_data(icao_code="LGTS"):
    """
    Fetches the latest official raw METAR data from the NOAA Aviation Weather API.

    Args:
        icao_code (str): The ICAO code of the target airport.

    Returns:
        tuple: A string containing the raw METAR and a single-row DataFrame.
    """
    url = f"https://aviationweather.gov/api/data/metar?ids={icao_code}&format=json"
    
    raw_metar = None
    raw_metar_df = pd.DataFrame() 
    
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        if isinstance(data, list) and len(data) > 0:
            metar_info = data[0]
            raw_metar = metar_info.get("rawOb") 
            raw_metar_df = pd.DataFrame({"metar": [raw_metar]})
        else:
            st.warning(f"No METAR data found for the specified ICAO code: {icao_code}.")
    else:
        st.error(f"Failed to fetch METAR data. Status code: {response.status_code}")

    return raw_metar, raw_metar_df


#---- ML Model Creation and Prediction Section ----#

def preprocess_data(columns_to_encode):
    """
    Constructs a scikit-learn ColumnTransformer to apply One-Hot Encoding 
    to categorical features while passing through numerical features.

    Args:
        columns_to_encode (list): List of categorical column names to encode.

    Returns:
        ColumnTransformer: The configured scikit-learn preprocessing transformer.
    """
    preprocess = ColumnTransformer(
        transformers=[
            ('onehot', OneHotEncoder(handle_unknown='ignore'), columns_to_encode)
        ],
        remainder='passthrough'
    )

    return preprocess 

def calculate_random_forest(trees, depth, min_samples_leaf, class_weight, preprocess, X_train, y_train):
    """
    Defines, compiles, and trains a Random Forest Classifier pipeline.

    Args:
        trees (int): Number of estimators (trees) in the forest.
        depth (int): Maximum depth of the trees.
        min_samples_leaf (int): Minimum number of samples required to be at a leaf node.
        class_weight (str): Weights associated with classes to handle imbalance.
        preprocess (ColumnTransformer): The preprocessing steps for the pipeline.
        X_train (pd.DataFrame): Training feature set.
        y_train (pd.Series): Target variable (runway configuration).

    Returns:
        Pipeline: The trained scikit-learn model pipeline.
    """
    runway_pipeline = Pipeline(steps=[
        ('preprocess', preprocess),
        ('classifier', RandomForestClassifier(
            n_estimators=trees,               
            max_depth=depth,                  
            min_samples_leaf=min_samples_leaf, 
            min_samples_split=10,             
            max_features='sqrt',              
            bootstrap=True,                   
            oob_score=True,                   
            random_state=42,                  
            n_jobs=-1                         
        ))
    ])

    runway_pipeline.fit(X_train, y_train)
    return runway_pipeline

def data_ml_conversion(df):
    """
    Prepares and transforms features for ML modeling, including cyclical 
    encoding (sine/cosine) for continuous temporal and directional data.

    Args:
        df (pd.DataFrame): The feature dataframe.

    Returns:
        pd.DataFrame: The transformed dataframe ready for the ML pipeline.
    """
    # Replace NaN values with large numbers to indicate "no ceiling" or "no clouds"
    df['ceiling_height'] = df['ceiling_height'].fillna(100000)
    df['min_clouds_height'] = df['min_clouds_height'].fillna(100000)
    df['hour'] = df['hour'].dt.hour

    # Cyclical encoding
    df['wind_dir_sin'] = np.sin(2 * np.pi * df['wind_dir'] / 360)
    df['wind_dir_cos'] = np.cos(2 * np.pi * df['wind_dir'] / 360)
    df['hour_sin'] = np.sin(2 * np.pi * df['hour'] / 24)
    df['hour_cos'] = np.cos(2 * np.pi * df['hour'] / 24)

    df.drop(columns=['wind_dir', 'hour'], inplace=True)
    return df

def set_data():
    """
    Connects to the database, retrieves historical feature data, applies ML 
    conversions, and identifies categorical columns.

    Returns:
        tuple: The processed dataframe and a list of categorical column names.
    """
    load_dotenv()
    engine = create_engine(os.getenv('DB_URL'))
    
    query = """SELECT wind_dir, wind_speed, is_wind_vrb,
    min_clouds_height, ceiling_height, ceiling_category,
    weather_intensity, weather_category,
    season, hour, is_night,
    runway_config FROM final_features order by timestamp"""

    df = pd.read_sql(query, engine)
    df = data_ml_conversion(df)

    categorical_columns = ['weather_category', 'weather_intensity', 'season', 'ceiling_category']

    return df, categorical_columns
    
@st.cache_resource()
def create_model():
    """
    Orchestrates the entire ML setup: loads data, isolates features/targets, 
    initializes the preprocessor, and trains the Random Forest pipeline.

    Returns:
        tuple: The fully trained pipeline and the list of feature column names.
    """
    df, categorical_columns = set_data()

    X = df.drop(['runway_config'], axis=1)
    y = df['runway_config']

    preprocess = preprocess_data(categorical_columns)

    runway_rf_pipeline = calculate_random_forest(
        trees=300, 
        depth=8, 
        min_samples_leaf=5, 
        class_weight='balanced', 
        preprocess=preprocess, 
        X_train=X, 
        y_train=y
    )

    return runway_rf_pipeline, X.columns

def runway_prediction(currentX, runway_rf_pipeline):
    """
    Predicts the active runway configuration based on current/forecasted features.

    Args:
        currentX (pd.DataFrame): The current situational feature set.
        runway_rf_pipeline (Pipeline): The trained ML model.

    Returns:
        array: The predicted runway configuration identifier.
    """
    predicted_runway = runway_rf_pipeline.predict(currentX)
    return predicted_runway