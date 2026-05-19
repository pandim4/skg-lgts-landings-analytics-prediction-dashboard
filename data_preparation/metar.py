import pandas as pd
import re

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
    datacoles={"name":["time","wind","varyingwind","visibility","lvisibility","rvisibility","weather","clouds","temperature","pressure","cavok","trend"],
            "re":[r".*Z$",r"([0-9]{3}|VRB)([0-9]{2})(G([0-9]{2}))?KT$",r"([0-9]+)V([0-9]+)$",r"[0-9]{4}$",r"([0-9]{4})((N|S|E|W)+)$",
                    r"R([0-9]{2})/([0-9]{4})$",r"(\+|\-|VC)?((RE|MI|PR|BC|DR|BL|SH|TS|FZ)*)((DZ|RA|SN|SG|GS|GR|PL|IC|UP)*)((FG|BR|HZ|VA|DU|FU|SA|PY)*)((SQ|PO|DS|SS|FC)*)$",
                    r"(FEW|SCT|BKN|OVC)([0-9]{3})(TCU|CB)?$",r"(M)?([0-9]+)/(M)?([0-9]+)$",r"Q([0-9]{4})$",r"CAVOK",r"(NOSIG|TEMPO|BECMG)"]}

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

    temp_data={}
    final_data={}

    for k,name in enumerate(final_datacoles["name"]):
        temp_data[name]={}
        final_data[name]=[]
        
    parts = df["metar"].iloc[0].split()
    data={}

    for k,name in enumerate(datacoles["name"]):
        data[name]={"values": [], "positions": []}
     
    for j in range (len(parts)):
       for m in range (len(datacoles["re"])):
        current = re.match(datacoles["re"][m],parts[j])
        if(current!=None):
            data[datacoles["name"][m]]["values"].append(current)
            data[datacoles["name"][m]]["positions"].append(j)

    for k,name in enumerate(final_datacoles["name"]):
       temp_data[name]=None
     
    recorded=False
    if(data["trend"]["values"]!=[]):
       trend_data=data["trend"]["values"][0]
       trend_position=data["trend"]["positions"][0]
       recorded=True
    
    temp_data["trend_status"]=0
    if(recorded):
       if(trend_data.group()=="BECMG"):
         temp_data["trend_status"]=1
       if(trend_data.group()=="TEMPO"):
          temp_data["trend_status"]=2

    def is_trendy(name):
        if name!="clouds":
          return (temp_data["trend_status"]!=0 and (len(data[name]["values"])>1))
        else:
          return (temp_data["trend_status"]!=0) and (len(data[name]["values"])>1) and (max(data[name]["positions"])>trend_position)
           
    cavok_recorded=False
    if(data["cavok"]["values"]!=[]):
       trend_data=data["cavok"]["values"][0]
       temp_data["cavok_recorded"]=True
        
    def default_wind():
       temp_data["wind_dir"]=int(wind_data[0].group(1)) if wind_data[0].group(1)!="VRB" else -1
       temp_data["wind_speed"]=int(wind_data[0].group(2))
       temp_data["wind_gusts"]=int(wind_data[0].group(4)) if wind_data[0].group(3)!=None else None

    def trendy_wind():
       default_wind()
       temp_data["extra_wind_dir"]=int(wind_data[1].group(1)) if wind_data[1].group(1)!="VRB" else -1
       temp_data["extra_wind_speed"]=int(wind_data[1].group(2))
       temp_data["extra_wind_gusts"]=int(wind_data[1].group(4)) if wind_data[1].group(3)!=None else None

    wind_data=data["wind"]["values"]  
    if is_trendy("wind"): trendy_wind()
    else: default_wind()
        
    recorded=False
    if(data["varyingwind"]["values"]!=[]):
        varyingwind_data=data["varyingwind"]["values"][0]
        recorded=True

    if(recorded):
        temp_data["varying_wind_from"]=int(varyingwind_data.group(1))
        temp_data["varying_wind_to"]=int(varyingwind_data.group(2))

    def default_visibility():
        temp_data["visibility"]=int(visibility_data[0].group())

    def trendy_visibility():
        default_visibility()
        temp_data["extra_visibility"]=int(visibility_data[1].group())
  
    recorded=False
    if(data["visibility"]["values"]!=[]):
        recorded=True
        visibility_data=data["visibility"]["values"]

    if(recorded):
        if is_trendy("visibility"):trendy_visibility()
        else: default_visibility()
    else: 
        if (temp_data["cavok_recorded"]):
            temp_data["visibility"]=int(9999)

    recorded=False
    if(data["lvisibility"]["values"]!=[]):
        local_visibility_data=data["lvisibility"]["values"][0]
        recorded=True
    
    if(recorded):
        temp_data["local_visibility"]=int(local_visibility_data.group(1))
        temp_data["local_visibility_dir"]=local_visibility_data.group(2) 

    recorded=False
    if(data["rvisibility"]["values"]!=[]):
        runway_visibility_data=data["rvisibility"]["values"]
        recorded=True

    if(recorded):
        records=len(runway_visibility_data)  
        temp_data["runway1_id"]=int(runway_visibility_data[0].group(1))
        temp_data["runway1_visibility"]=int(runway_visibility_data[0].group(2))
        temp_data["runway2_id"]=int(runway_visibility_data[1].group(1)) if records>1 else None
        temp_data["runway2_visibility"]=int(runway_visibility_data[1].group(2)) if records>1 else None

    temperature_data=data["temperature"]["values"][0]
    temperature_sign=-1 if(temperature_data.group(1))=="M" else 1
    dew_point_sign=-1 if(temperature_data.group(3))=="M" else 1       
    temp_data["temperature"]=int(temperature_data.group(2))*temperature_sign
    temp_data["dew_point"]=int(temperature_data.group(4))*dew_point_sign

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

    recorded=False
    if(data["weather"]["values"]!=[]):
        recorded=True
        weather_data=data["weather"]["values"]

    if(recorded):
        if(is_trendy("weather")):trendy_weather()
        else: default_weather()          

    recorded=False
    if(data["pressure"]["values"]!=[]):
        pressure_data=data["pressure"]["values"][0]
        recorded=True

    if(recorded):
        temp_data["pressure"]=int(pressure_data.group(1))

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
        
    recorded=False
    if(data["clouds"]["values"]!=[]):
        clouds_data=data["clouds"]["values"]
        recorded=True

    if(recorded):
        if(is_trendy("clouds")): trendy_clouds()
        else: default_clouds()

    for k,name in enumerate(final_datacoles["name"]):
        final_data[name].append(temp_data[name])
    
    fdf = pd.DataFrame(final_data)
    fdf.insert(0, "time", df["date"].values[0])

    return fdf

def parse_multiple_metars(df):
    """
    Iterates over a DataFrame with multiple rows and parses each individual METAR string.

    Args:
        df (pd.DataFrame): DataFrame containing multiple records with 'metar' and 'date' columns.

    Returns:
        pd.DataFrame: A combined DataFrame containing parsed data for all rows.
    """
    results = []
    for i in range(len(df)):
        single_row_df = pd.DataFrame(df.iloc[i]).transpose()
        parsed_row_df = metar_parser(single_row_df)
        results.append((parsed_row_df))
    
    final_df = pd.concat(results, ignore_index=True)
    return final_df