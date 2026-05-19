# This module contains functions for feature engineering, METAR parsing, and machine learning model creation and prediction.
import numpy as np
import pandas as pd


#-----Features Creation-----#

###Time features###

from astral import LocationInfo
from astral.sun import sun
import holidays


gr_holidays = holidays.Greece(years=[2024])
city = LocationInfo(name="Thessaloniki", region="Greece", timezone="Europe/Athens", latitude=40.6401, longitude=22.9444)

def is_night(fg):

    s = sun(city.observer, date=fg['timestamp'].date(), tzinfo=city.timezone)

    local_tz=fg['timestamp'].tz_convert('Europe/Athens')
    
    return (local_tz < s['sunrise']) or (local_tz > s['sunset'])

def calendar_season(month):

    winter=set([12,1,2])
    spring=set([3,4,5])
    summer=set([6,7,8])
    autumn=set([9,10,11])
    
    if month in (winter):
        return 'Winter'
    elif month in (spring):
        return  'Spring'
    elif month in (summer):
        return 'Summer'
    elif month in (autumn):
        return 'Autumn'


def day_period(h):
    
    local_hour = h.tz_convert('Europe/Athens').hour
    
    # mapping σε periods
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
    current_year = pd.Timestamp.now().year
 
    landings_df['monthday']=landings_df['timestamp'].dt.day
    
    landings_df['weekday']=landings_df['timestamp'].dt.dayofweek
    
    landings_df['day_period'] = landings_df['hour'].apply(day_period)
    
    landings_df['month']=landings_df['timestamp'].dt.month
    
    landings_df['season'] = landings_df['month'].apply(calendar_season)
    
    landings_df['calendar'] = np.where((landings_df['timestamp'] < pd.Timestamp(current_year, 3, 31,tz='UTC')) | (landings_df['timestamp'] > pd.Timestamp(current_year, 10, 27,tz='UTC'))  , 'Winter', 'Summer')
    
    landings_df['is_night']= landings_df.apply(is_night, axis=1)
    
    landings_df['is_holiday'] = landings_df['timestamp'].dt.date.isin(gr_holidays)

    return landings_df


###Weather features###


###Wind Section###
def calculate_winds(df):
    
    #Wind Gusts Features
    df['wind_gusts']=df['wind_gusts'].fillna(df['wind_speed'])
    df['gust_factor']= df['wind_gusts']/df['wind_speed']
    df['gust_delta']= df['wind_gusts'] - df['wind_speed']
    df['is_wind_gusty']=(df['gust_factor'] > 1).astype(bool)

    #Varying Wind Features
    df['is_wind_vrb']=(df['wind_dir'] == -1).astype(bool)
    df['varying_spread'] = (df['varying_wind_to'] - df['varying_wind_from']) % 360
    df['varying_spread'] = df['varying_spread'].fillna(0)

    #Vardaris Feature
    vardaris_direction=340
    df['is_wind_vardaris'] = (abs((df['wind_dir'] - vardaris_direction + 180) % 360 - 180)<=30) & ((df['wind_speed']>=15) | (df['gust_factor']>1))

    #Sea Breeze Feature
    sea_breeze_direction=180
    df['is_wind_sea_breeze'] = (abs((df['wind_dir'] - sea_breeze_direction + 180) % 360 - 180)<=30) & (df['wind_speed'].between(3, 15))

    #Wind Speed Category
    def wind_speed_category(speed):
        if speed < 5:
            return "Calm"
        elif speed < 15:
            return "Light"
        elif speed < 25:
            return "Moderate"
        elif speed < 35:
            return "Strong"
        else:
            return "Very Strong"
    
    df['wind_speed_category'] = df['wind_speed'].apply(wind_speed_category)

    #Wind Direction Category
    def wind_direction_category(direction):
        if direction == -1:
            return "Variable"
        direction = direction % 360
        if 337.5 <= direction or direction < 22.5:
            return "North"
        elif 22.5 <= direction < 67.5:
            return "Northeast"
        elif 67.5 <= direction < 112.5:
            return "East"
        elif 112.5 <= direction < 157.5:
            return "Southeast"
        elif 157.5 <= direction < 202.5:
            return "South"
        elif 202.5 <= direction < 247.5:
            return "Southwest"
        elif 247.5 <= direction < 292.5:
            return "West"
        elif 292.5 <= direction < 337.5:
            return "Northwest"
    
    df['wind_direction_category'] = df['wind_dir'].apply(wind_direction_category)

    #Wind per runway.
    runways=[104,284,166,346]

    speed = df['wind_speed'].copy()
    direction = df['wind_dir'].copy()
    speed[df['is_wind_vrb']] = 0
    direction[df['is_wind_vrb']] = 0

   
    for runway in runways:
        radians=np.radians(direction-runway)
        df[f'headwind_{runway//10}']= speed * np.cos(radians)
        df[f'crosswind_{runway//10}']= speed * np.sin(radians)

    
###Weather phenomena section###
def calculate_weather_phenomena(df):
    
    intensity_map={'-1':'Light','2':'Heavy'}
    df['weather_intensity']=df['weather_intensity'].map(intensity_map)
    mask=(df['weather_intensity'].isna()) & (df[['weather_descriptor','weather_precipitation','weather_obscuration']]).notna().any(axis=1)
    df.loc[mask,'weather_intensity']='Moderate'
    df['weather_intensity']=df['weather_intensity'].fillna('No')

    weather_category=  [
    df['weather_descriptor'] == 'TS',                                     
    df['weather_obscuration'] == 'FG',                                   
    (df['weather_precipitation'] == 'RA') | (df['weather_descriptor'] == 'SH'), 
    df['weather_precipitation'] == 'DZ',                                  
    df['weather_obscuration'] == 'BR',                                   
    df['weather_precipitation'].isna() & df['weather_descriptor'].isna() & df['weather_obscuration'].isna() # 6. Καθαρός
    ]

    categories = ['Thunderstorm', 'Fog', 'Rain', 'Drizzle', 'Mist', 'Clear']
    df['weather_category'] = np.select(weather_category, categories, default='Other')


def visibility_category(visibility):

    if  visibility < 300:
        return "Critical"
    elif visibility <= 800:
        return "Low"
    elif  visibility < 5000:
        return "Medium"
    else:
        return "High"

def temperature_category(temperature):
    if  temperature < 0:
        return "Very Cold"
    elif temperature < 10:
        return "Cold"
    elif  temperature < 20:
        return "Mild"
    elif  temperature < 30:
        return "Warm"
    else:
        return "Hot"

def pressure_category(pressure):
    if  pressure < 990:
        return "Very Low"
    elif pressure < 1005:
        return "Low"
    elif  pressure < 1020:
        return "Normal"
    elif  pressure < 1030:
        return "High"
    else:
        return "Very High"


def ceiling_category(ceil, visibility=None):
    if pd.isna(ceil):
        return "VFR"
        
    if ceil < 500 or visibility < 1500:    
        return 'LIFR'
    elif ceil < 1000 or visibility < 5000:
        return 'IFR'
    elif ceil <= 3000 or visibility < 8000: 
        return 'MVFR'
    else:
        return 'VFR'


def calculate_clouds(df):

   height_columns=['cloud1_height', 'cloud2_height', 'cloud3_height']
   amount_columns=['cloud1_amount', 'cloud2_amount', 'cloud3_amount']
   formation_columns=['cloud1_formation', 'cloud2_formation', 'cloud3_formation']
    

   df['min_clouds_height'] = df[height_columns].min(axis=1)
   df['clouds_layers'] = df[height_columns].count(axis=1)

   ceiling_values=['BKN','OVC']


   temp_heights = df[height_columns].where(df[amount_columns].isin(ceiling_values).values)
   df['ceiling_height'] = temp_heights.min(axis=1)
   df['is_ceiling'] = df['ceiling_height'].notna()
   df['ceiling_category'] = df[['ceiling_height', 'visibility']].apply(lambda x: ceiling_category(x['ceiling_height'], x['visibility']), axis=1)


   convective_values=['CB','TCU']
   temp_heights = df[height_columns].where(df[formation_columns].isin(convective_values).values)
   df['convective_height'] = temp_heights.min(axis=1)
   df['is_convective'] = df['convective_height'].notna()

  
   return df

def calculate_weather_features(weather_df):
    #Apply the functions for features creation.    
        
    #Wind
    calculate_winds(weather_df)

    #Weather_phenomena
    calculate_weather_phenomena(weather_df)

    #Clouds
    calculate_clouds(weather_df)

    #Visibility
    weather_df['visibility_category'] = weather_df['visibility'].apply(visibility_category)

    #Temperature
    weather_df['temperature_category'] = weather_df['temperature'].apply(temperature_category)

    #Pressure
    weather_df['pressure_category'] = weather_df['pressure'].apply(pressure_category)

    #Drop type column because it is not useful now.
    weather_df = weather_df.drop(columns=['wind_gusts','weather_descriptor','weather_precipitation','weather_obscuration','cloud1_height', 'cloud2_height', 'cloud3_height','cloud1_amount', 'cloud2_amount', 'cloud3_amount','cloud1_formation', 'cloud2_formation', 'cloud3_formation'])

    #Set findal df order.
    timestamp=['timestamp']
    wind=['wind_dir','wind_direction_category','wind_speed','wind_speed_category','is_wind_vrb','varying_spread','varying_wind_from','varying_wind_to','is_wind_gusty','gust_factor','gust_delta','is_wind_vardaris','is_wind_sea_breeze','headwind_10','crosswind_10','headwind_28','crosswind_28','headwind_16','crosswind_16','headwind_34','crosswind_34']
    weather_phenomena=['weather_intensity','weather_category']
    other=['temperature','temperature_category','dew_point','visibility','visibility_category','pressure','pressure_category']
    clouds=['min_clouds_height','clouds_layers','is_ceiling','ceiling_height','ceiling_category','is_convective','convective_height']
    columns_order = timestamp + wind + weather_phenomena + other + clouds
    weather_df = weather_df.reindex(columns=columns_order)

    return weather_df


#---- METAR Parsing Section ----#

# This function takes a DataFrame with a 'metar' column and extracts various features from the METAR string using regular expressions. It returns a new DataFrame with the extracted features as columns.
def metar_parser(df):

    #Instert regional expressions
    import re

    #Names of the METAR components and their corresponding regex tokens
    datacoles={"name":["time","wind","varyingwind","visibility","lvisibility","rvisibility","weather","clouds","temperature","pressure","cavok","trend"],
            "re":[r".*Z$",r"([0-9]{3}|VRB)([0-9]{2})(G([0-9]{2}))?KT$",r"([0-9]+)V([0-9]+)$",r"[0-9]{4}$",r"([0-9]{4})((N|S|E|W)+)$",
                    r"R([0-9]{2})/([0-9]{4})$",r"(\+|\-|VC)?((RE|MI|PR|BC|DR|BL|SH|TS|FZ)*)((DZ|RA|SN|SG|GS|GR|PL|IC|UP)*)((FG|BR|HZ|VA|DU|FU|SA|PY)*)((SQ|PO|DS|SS|FC)*)$",
                    r"(FEW|SCT|BKN|OVC)([0-9]{3})(TCU|CB)?$",r"(M)?([0-9]+)/(M)?([0-9]+)$",r"Q([0-9]{4})$",r"CAVOK",r"(NOSIG|TEMPO|BECMG)"]}

    #The names of the final data which will be the coles of the final dataFrame.
    final_datacoles={"name":["wind_dir","wind_speed","wind_gusts","varying_wind_from","varying_wind_to",
                            "visibility","local_visibility","local_visibility_dir","runway1_id","runway1_visibility","runway2_id","runway2_visibility",
                            "temperature","dew_point",
                            "weather_intensity","weather_descriptor","weather_precipitation","weather_obscuration","weather_other",
                            "pressure",
                            "cavok_recorded","trend_status",
                            "cloud1_amount","cloud1_height","cloud1_formation","cloud2_amount","cloud2_height","cloud2_formation","cloud3_amount","cloud3_height","cloud3_formation",
                            "extra_wind_dir","extra_wind_speed","extra_wind_gusts",
                            "extra_visibility",
                            "extra_weather_intensity","extra_weather_descriptor","extra_weather_precipitation","extra_weather_obscuration","extra_weather_other",
                            "extra_cloud1_amount","extra_cloud1_height","extra_cloud1_formation","extra_cloud2_amount","extra_cloud2_height","extra_cloud2_formation"
                            ]}

    #Initialize an empty temp_data dictionary which will temporarly store the data that will be extracted from every row
    temp_data={}

    #Initialize an empty final_data dictionary which will store the total of the data that will be extracted from all the rows
    final_data={}

    # Create sub-dictionaries and sub-lists using the names from the final DataFrame columns as keys
    for k,name in enumerate(final_datacoles["name"]):
        temp_data[name]={}
        final_data[name]=[]
        

    parts = df["metar"].iloc[0].split() #Split the metar in parts 
    data={} #Create a new data dictionary which will store the recognized tokens 

    #Create multiple sub-dictionaries with key the METAR component name and store the recognized token value or values and their position 
    for k,name in enumerate(datacoles["name"]):
        data[name]={"values": [], "positions": []}
     
    for j in range (len(parts)): #Get every part of the row
       for m in range (len(datacoles["re"])): #Get every regex
        current = re.match(datacoles["re"][m],parts[j]) #Compare the current part with all the regex
        if(current!=None): #if there is a match
            data[datacoles["name"][m]]["values"].append(current) #add the recognized token to the list
            data[datacoles["name"][m]]["positions"].append(j) #add the recognized token position to the list


    ##VARIABLES INITIALIZATION
    for k,name in enumerate(final_datacoles["name"]): #Initialize in every loop the values of the temp_data=None
       temp_data[name]=None
     
    
    
    ##TREND SECTION
    recorded=False # False for no record
    if(data["trend"]["values"]!=[]): #if trend recorded
       trend_data=data["trend"]["values"][0]
       trend_position=data["trend"]["positions"][0]
       recorded=True
    
    temp_data["trend_status"]=0 # 0 for NOSIG or default METAR
    if(recorded): #No trend recorded
       if(trend_data.group()=="BECMG"):
         temp_data["trend_status"]=1 # 1 for BECMG
       if(trend_data.group()=="TEMPO"):
          temp_data["trend_status"]=2 # 2 for TEMPO

    def is_trendy(name): #This function will be used to check if a token has the default form in the METAR or not
        if name!="clouds":
          return (temp_data["trend_status"]!=0 and (len(data[name]["values"])>1))
        else:
          return (temp_data["trend_status"]!=0) and (len(data[name]["values"])>1) and (max(data[name]["positions"])>trend_position)
           
    ##CAVOK SECTION
    
    # Used if: Visibility greater or equal to 10 km and the lowest visibility is not reported, 
    #no cumulonimbus or towering cumulus, no cloud below 5000 ft or highest minimum sector altitude (MSA)( whichever is the greater) 
    #and no weather significant to aviation
    
    cavok_recorded=False # False for no CAVOK record
    if(data["cavok"]["values"]!=[]): #if CAVOK recorded
       trend_data=data["cavok"]["values"][0]
       temp_data["cavok_recorded"]=True
        
    
    ##WIND SECTION

    def default_wind():
       
       temp_data["wind_dir"]=int(wind_data[0].group(1)) if wind_data[0].group(1)!="VRB" else -1 # -1 for VRB
       temp_data["wind_speed"]=int(wind_data[0].group(2))
       temp_data["wind_gusts"]=int(wind_data[0].group(4)) if wind_data[0].group(3)!=None else None

    def trendy_wind():
       
       default_wind()
        
       temp_data["extra_wind_dir"]=int(wind_data[1].group(1)) if wind_data[1].group(1)!="VRB" else -1 # -1 for VRB
       temp_data["extra_wind_speed"]=int(wind_data[1].group(2))
       temp_data["extra_wind_gusts"]=int(wind_data[1].group(4)) if wind_data[1].group(3)!=None else None

    wind_data=data["wind"]["values"]  
    if is_trendy("wind"): trendy_wind()
    else: default_wind()
        
    ##VARYING WIND SECTION
    recorded=False # False for no record
    if(data["varyingwind"]["values"]!=[]): #if varying wind recorded
        varyingwind_data=data["varyingwind"]["values"][0]
        recorded=True

    if(recorded):
        temp_data["varying_wind_from"]=int(varyingwind_data.group(1))
        temp_data["varying_wind_to"]=int(varyingwind_data.group(2))

      #print(wind_dir,wind_speed,wind_gusts,varying_wind_from,varying_wind_to,i)
        

    ##VISIBILITY SECTION

    def default_visibility():
        temp_data["visibility"]=int(visibility_data[0].group())

    def trendy_visibility():
        default_visibility()
        temp_data["extra_visibility"]=int(visibility_data[1].group())
  
        
    recorded=False # False for no record
    if(data["visibility"]["values"]!=[]): #if visibility recorded
        recorded=True
        visibility_data=data["visibility"]["values"]
    

    if(recorded):
        if is_trendy("visibility"):trendy_visibility()
        else: default_visibility()
    else: 
        if (temp_data["cavok_recorded"]):
            temp_data["visibility"]=int(9999)
           #print(visibility,"C",i)

    ##LOCAL VISIBILITY SECTION #MAX 1 LOCAL VISIBILITY IN MY DATA
    recorded=False # False for no record
    if(data["lvisibility"]["values"]!=[]): #if local visibility recorded
        local_visibility_data=data["lvisibility"]["values"][0]
        recorded=True
    
    if(recorded):
        temp_data["local_visibility"]=int(local_visibility_data.group(1))
        temp_data["local_visibility_dir"]=local_visibility_data.group(2) 
          
    #print(lvisibility,lvisibility_dir,i)

    ##RUNWAY VISIBILITY SECTION #MAX 2 RUNWAY VISIBILITY IN MY DATA
    recorded=False # False for no record
    if(data["rvisibility"]["values"]!=[]): #if runway visibility recorded
        runway_visibility_data=data["rvisibility"]["values"]
        recorded=True
    

    if(recorded):
        records=len(runway_visibility_data)  
        temp_data["runway1_id"]=int(runway_visibility_data[0].group(1))
        temp_data["runway1_visibility"]=int(runway_visibility_data[0].group(2))
        temp_data["runway2_id"]=int(runway_visibility_data[1].group(1)) if records>1 else None
        temp_data["runway2_visibility"]=int(runway_visibility_data[1].group(2)) if records>1 else None

          
    #print(rvisibility1,rvisibility_id1,rvisibility2,rvisibility_id2,i)
      

    ##TEMPERATURE SECTION
    temperature_data=data["temperature"]["values"][0]
        
    temperature_sign=-1 if(temperature_data.group(1))=="M" else 1
    dew_point_sign=-1 if(temperature_data.group(3))=="M" else 1       
    temp_data["temperature"]=int(temperature_data.group(2))*temperature_sign
    temp_data["dew_point"]=int(temperature_data.group(4))*dew_point_sign

    #print(temperature,dew_point)


    ##WEATHER SECTION
    def default_weather():
        if (weather_data[0].group(1)!=None):
            temp_data["weather_intensity"]=1 if weather_data[0].group(1)=="+" else -1
            temp_data["weather_intensity"]=2 if weather_data[0].group(1)=="VC" else -1
        temp_data["weather_descriptor"]=weather_data[0].group(3)
        temp_data["weather_precipitation"]=weather_data[0].group(5)
        temp_data["weather_obscuration"]=weather_data[0].group(7)
        temp_data["weather_other"]=weather_data[0].group(9)
        
    def trendy_weather():
        
        default_weather()

        if (weather_data[1].group(1)!=None):
            temp_data["extra_weather_intensity"]=1 if weather_data[1].group(1)=="+" else -1
            temp_data["extra_weather_intensity"]=2 if weather_data[1].group(1)=="VC" else -1
        temp_data["extra_weather_descriptor"]=weather_data[1].group(3)
        temp_data["extra_weather_precipitation"]=weather_data[1].group(5)
        temp_data["extra_weather_obscuration"]=weather_data[1].group(7)
        temp_data["extra_weather_other"]=weather_data[1].group(9)


    
    recorded=False # False for no record
    if(data["weather"]["values"]!=[]): #if WEATHER recorded
        recorded=True
        weather_data=data["weather"]["values"]

    if(recorded):
        if(is_trendy("weather")):trendy_weather()
        else: default_weather()          
       
        #print(weather_intensity,weather_descriptor,weather_precipitation,weather_obscuration,weather_other)  

    ##PRESSURE SECTION
    recorded=False # False for no record
    if(data["pressure"]["values"]!=[]): #if PRESSURE recorded
        pressure_data=data["pressure"]["values"][0]
        recorded=True

    if(recorded):
        temp_data["pressure"]=int(pressure_data.group(1))


    #print(pressure)  

    ##CLOUDS SECTION
    def default_clouds():
        for k,cloud in enumerate(clouds_data):
          if(k<3):
           temp_data[f"cloud{k+1}_amount"]=cloud.group(1)
           temp_data[f"cloud{k+1}_height"]=int(cloud.group(2))*100
           temp_data[f"cloud{k+1}_formation"]=cloud.group(3)

    def trendy_clouds():

        default_clouds()

        for k,cloud in enumerate(clouds_data):
          if(k>=3):
           temp_data[f"extra_cloud{k-2}_amount"]=cloud.group(1)
           temp_data[f"extra_cloud{k-2}_height"]=int(cloud.group(2))*100
           temp_data[f"extra_cloud{k-2}_formation"]=cloud.group(3)
        
        
    recorded=False # False for no record
    if(data["clouds"]["values"]!=[]): #if PRESSURE recorded
        clouds_data=data["clouds"]["values"]
        recorded=True

    if(recorded):
        if(is_trendy("clouds")): trendy_clouds()
        else: default_clouds()

        #print(cloud2_amount,cloud2_height,cloud2_formation,i)
    


    for k,name in enumerate(final_datacoles["name"]):
        final_data[name].append(temp_data[name])
    
    #print(i,
         # temp_data["wind_dir"],wind_speed,wind_gusts,
        #  varying_wind_from,varying_wind_to,
         # visibility,
         # temperature,dew_point,
        # weather_intensity,weather_descriptor,weather_precipitation,weather_obscuration,weather_other,
        #  pressure)
    fdf = pd.DataFrame(final_data)

    return fdf

import requests
from datetime import datetime, timezone
import streamlit as st

# This function retrieves METAR forecast data from the Open-Meteo API for a specified location and station. It processes the hourly forecast data to extract relevant weather features and constructs METAR-like strings for specific time intervals. The resulting data is returned as a DataFrame.
import pandas as pd
import requests
from datetime import datetime, timezone

@st.cache_data(ttl=3600)
def get_metar_forecast_df(lat=40.52, lon=22.97, station="LGTS"):
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
    # 0=Clear, 1-3=Cloudy, 51-67=Rain/Drizzle, 71-77=Snow, 80-82=Showers, 95-99=TS
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

        # 1. Time and Wind
        ts = datetime.strptime(time_val, "%Y-%m-%dT%H:%M").strftime("%d%H%MZ")
        wind_str = f"{int(w_dir):03d}{int(w_spd_kt):02d}KT"
        
        # 2. Visibility
        vis_str = "9999" if vis_m >= 9999 else f"{int(vis_m):04d}"
        
        # 3. Weather
        weather_str = wmo_to_metar.get(w_code, "")

        # 4. Sky Condition
        if c_base is None or c_cov < 10:
            sky_str = "" 
        else:
            alt = int(c_base * 3.28 / 100)
            pre = "FEW" if c_cov < 25 else "SCT" if c_cov < 50 else "BKN" if c_cov < 85 else "OVC"
            sky_str = f"{pre}{alt:03d}"

        # Construct final string (Cleaned of double spaces)
        components = [station, ts, wind_str, vis_str, weather_str, sky_str, f"{int(temp):02d}/{int(dew):02d}", f"Q{int(qnh_val)}"]
        metar_string = " ".join([c for c in components if c])

        rows.append({
            "time": time_val,
            "metar": metar_string,
        })

    return pd.DataFrame(rows)

@st.cache_data(ttl=900)
def get_metar_data(icao_code="LGTS"):
    # Το επίσημο και δωρεάν API της αμερικανικής κυβέρνησης (NOAA)
    url = f"https://aviationweather.gov/api/data/metar?ids={icao_code}&format=json"
    
    # Αρχικοποίηση μεταβλητών για την αποφυγή σφαλμάτων αν αποτύχει το request
    raw_metar = None
    raw_metar_df = pd.DataFrame() 
    
    # Κάνουμε το request (δεν χρειάζονται headers/API keys)
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        
        # Η NOAA επιστρέφει απευθείας μια λίστα με λεξικά
        if isinstance(data, list) and len(data) > 0:
            metar_info = data[0]
            # Το κλειδί για το ακατέργαστο METAR string στη NOAA είναι το "rawOb"
            raw_metar = metar_info.get("rawOb") 
            raw_metar_df = pd.DataFrame({"metar": [raw_metar]})
        else:
            st.warning(f"No METAR data found for the specified ICAO code: {icao_code}.")
    else:
        st.error(f"Failed to fetch METAR data. Status code: {response.status_code}")

    return raw_metar, raw_metar_df


#---- ML Model Creation and Prediction Section ----#

import streamlit as st
from sqlalchemy import create_engine
from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier


def preprocess_data(columns_to_encode):
    preprocess = ColumnTransformer(
        transformers=[
            ('onehot', OneHotEncoder(handle_unknown='ignore'), columns_to_encode)
        ],
        remainder='passthrough'
    )

    return preprocess 


def calculate_random_forest(trees, depth, min_samples_leaf, class_weight,preprocess,X_train,y_train):
    runway_pipeline = Pipeline(steps=[
    ('preprocess', preprocess),
    ('classifier', RandomForestClassifier(
        n_estimators=trees,         # Περισσότερα δέντρα για σταθερότητα (300 αντί για 100)
        max_depth=depth,              # Λίγο παραπάνω βάθος από το 6, αλλά όχι πάνω από 10
        min_samples_leaf=min_samples_leaf,       # Κάθε "φύλλο" να έχει τουλάχιστον 5 δείγματα (αποφεύγει το noise)
        #class_weight=class_weight,  # Κρίσιμο για να μην αγνοήσει τον διάδρομο 28

        min_samples_split=10,     # Μην σπας ένα group αν έχει κάτω από 10 δείγματα
        max_features='sqrt',      # Τυχαία επιλογή χαρακτηριστικών για κάθε δέντρο

        bootstrap=True,           # Χρήση τυχαίων υποσυνόλων των 1300 γραμμών
        oob_score=True,           # Χρήση των out-of-bag samples για εκτίμηση της απόδοσης

        random_state=42,          # Για να έχεις πάντα το ίδιο αποτέλεσμα
        n_jobs=-1                 # Ταχύτητα (χρήση όλων των πυρήνων)
    ))
])

    runway_pipeline.fit(X_train, y_train)

    return runway_pipeline

def data_ml_conversion(df):
    # Replace NaN values in ceiling_height and min_clouds_height with a large number (e.g., 100000) to indicate "no ceiling" or "no clouds"
    df['ceiling_height'] = df['ceiling_height'].fillna(100000)
    df['min_clouds_height'] = df['min_clouds_height'].fillna(100000)
    df['hour'] = df['hour'].dt.hour

    # Wind direction encoding
    df['wind_dir_sin'] = np.sin(2 * np.pi * df['wind_dir'] / 360)
    df['wind_dir_cos'] = np.cos(2 * np.pi * df['wind_dir'] / 360)

    #Hour encoding
    df['hour_sin'] = np.sin(2 * np.pi * df['hour'] / 24)
    df['hour_cos'] = np.cos(2 * np.pi * df['hour'] / 24)

    df.drop(columns=['wind_dir', 'hour'], inplace=True)

    return df

import os
from dotenv import load_dotenv
def set_data():
    #Get the data from the database
    load_dotenv()
    engine = create_engine(os.getenv('DB_URL'))
    
    query="""SELECT wind_dir,wind_speed,is_wind_vrb,
    min_clouds_height,ceiling_height,ceiling_category,
    weather_intensity,weather_category,
    season,hour,is_night,
    runway_config FROM final_features order by timestamp"""

    df = pd.read_sql(query, engine)
    df = data_ml_conversion(df)

    categorical_columns = ['weather_category', 'weather_intensity','season','ceiling_category']

    return df,categorical_columns
    

@st.cache_resource()
def create_model():
    
    # Set the data and categorical columns
    df,categorical_columns = set_data()

    # Prepare the data for modeling
    X = df.drop(['runway_config'], axis=1)
    y = df['runway_config']

    # Initialize the preprocessing pipeline (categorical columns to be encoded)
    preprocess = preprocess_data(categorical_columns)

    runway_rf_pipeline = calculate_random_forest(trees=300, depth=8, min_samples_leaf=5, class_weight='balanced',preprocess=preprocess,X_train=X,y_train=y)

    return runway_rf_pipeline,X.columns

def runway_prediction(currentX,runway_rf_pipeline):

    predicted_runway = runway_rf_pipeline.predict(currentX)

    return predicted_runway

