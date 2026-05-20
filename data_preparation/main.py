import os
import warnings
from datetime import datetime
import pandas as pd

from database import create_table_in_database, get_data_from_database
from preprocessing import apply_preprocessing_pipeline_landings, apply_preprocessing_weather, apply_preprocessing_aircrafts_airlines
from features import calculate_weather_features, calculate_landing_features,calculate_landing_features_extended,calculate_aircraft_features, merge_features

warnings.filterwarnings("ignore")

os.chdir(os.path.dirname(os.path.abspath(__file__)))
os.makedirs("data/input/quarters_of_landings_data", exist_ok=True)
os.makedirs("data/input", exist_ok=True)
os.makedirs("data/output", exist_ok=True)

#Load the raw data
print("Loading raw data...")
raw_landings_df = pd.read_csv("data/input/landings_data.csv")

raw_weather_df = pd.read_csv("data/input/weather_data.csv")

raw_aircrafts_df = pd.read_csv("data/input/aircrafts_data.csv", quotechar="'", on_bad_lines='skip', low_memory=False)
raw_aircrafts_df.columns = raw_aircrafts_df.columns.str.lower()

aircrafts_wtc_df = pd.read_csv("data/input/aircrafts_wtc_data.csv")

raw_airlines_df = pd.read_csv("data/input/airlines_data.csv")
raw_airlines_df.columns = raw_airlines_df.columns.str.lower()

######

#Apply the preprocessing pipelines and save the preprocessed data in the database.
print("Applying preprocessing pipelines...")
preprocessed_landings_df = apply_preprocessing_pipeline_landings(raw_landings_df, raw_aircrafts_df)

preprocessed_weather_df = apply_preprocessing_weather(raw_weather_df)

preprocessed_aircrafts_df, preprocessed_airlines_df = apply_preprocessing_aircrafts_airlines(raw_aircrafts_df, raw_airlines_df, preprocessed_landings_df)

print("Preprocessing completed. Saving preprocessed data in the database...")
create_table_in_database(preprocessed_landings_df, "landings")
create_table_in_database(preprocessed_weather_df, "weather")
create_table_in_database(preprocessed_aircrafts_df, "aircrafts")
create_table_in_database(aircrafts_wtc_df, "aircrafts_wtc")
create_table_in_database(preprocessed_airlines_df, "airlines")


######

#Calculate the features and save the final features dataframe in the database.

print("Calculating features...")
query_weather="""SELECT time as timestamp, wind_dir,wind_speed,wind_gusts,varying_wind_from,varying_wind_to, 
weather_descriptor,weather_intensity,weather_precipitation,weather_obscuration,
cloud1_height,cloud2_height,cloud3_height,cloud1_amount,cloud2_amount,cloud3_amount,cloud1_formation,cloud2_formation,cloud3_formation,
visibility,temperature,dew_point,pressure from weather"""

#Select the necessary columns from the aircrafts db that are needed for the features.
query_landings="""SELECT l.timestamp,l.icao24,l.callsign,a.name as airline,a.country,l.runway,l.date,l.hour  
FROM landings l LEFT JOIN airlines a
ON SUBSTR(l.callsign,1,3)=a.icao
ORDER BY l.timestamp
"""

query_landings_extended="""SELECT l.timestamp,l.icao24,l.callsign,a.name as airline,a.country,l.runway,l.date,l.hour,
l.latitude,l.longitude,l.groundspeed,l.vertical_rate,l.onground,l.alert,l.altitude,l.geoaltitude
FROM landings l LEFT JOIN airlines a
ON SUBSTR(l.callsign,1,3)=a.icao
ORDER BY l.timestamp
"""
query_aircrafts="select distinct al.icao24, al.manufacturericao  as manufacturer,al.typecode as models,al.icaoaircraftclass as type,aw.wtc as wtc from aircrafts al left join aircrafts_wtc aw  on al.typecode = aw.model order by models asc"

weather_features_df = calculate_weather_features(get_data_from_database(query_weather))
landing_features_df = calculate_landing_features(get_data_from_database(query_landings))
landing_features_extended_df = calculate_landing_features_extended(landing_features_df,get_data_from_database(query_landings_extended))
aircraft_features_df = calculate_aircraft_features(get_data_from_database(query_aircrafts))

print("Feature calculation completed. Saving features in the database...")
create_table_in_database(weather_features_df, "weather_features")
create_table_in_database(landing_features_df, "landings_features")
create_table_in_database(landing_features_extended_df, "landings_features_extended")
create_table_in_database(aircraft_features_df, "aircrafts_features")

#### 

print("Merging features and saving final dataframe in the database...")
#Merge the features and save the final dataframe in the database.

query1="SELECT * FROM landings_features order by timestamp"
query2="SELECT * FROM weather_features order by timestamp"
query3="SELECT * FROM aircrafts_features"
query4="SELECT * FROM landings_features_extended order by timestamp"

df_landings=get_data_from_database(query1)
df_weather=get_data_from_database(query2)
df_aircrafts=get_data_from_database(query3)
df_landings_extended=get_data_from_database(query4)

final_df, final_df_extended = merge_features(df_landings, df_weather, df_aircrafts, df_landings_extended)

create_table_in_database(final_df, 'final_features')
create_table_in_database(final_df_extended, 'final_features_extended')

print("All processes completed successfully.")