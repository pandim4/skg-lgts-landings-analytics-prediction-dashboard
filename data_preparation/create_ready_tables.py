import os
from dotenv import load_dotenv
import pandas as pd
from sqlalchemy import create_engine, text
load_dotenv()


def create_table_with_ddl(table_name, ddl_statement, df):
    """
    Creates a database table using the provided SQL DDL statement and loads data into it from a pandas DataFrame.

    Args:
        table_name (str): The name of the target database table.
        ddl_statement (str): The raw SQL string containing the CREATE TABLE statement.
        df (pd.DataFrame): The DataFrame containing the data to be inserted.
    """
    db_url = os.getenv('DB_URL')
    engine = create_engine(db_url)

    with engine.connect() as conn:
        print(f"Creating table '{table_name}'...")
        conn.execute(text(f"DROP TABLE IF EXISTS {table_name};"))
        conn.execute(text(ddl_statement))
        conn.commit() 
    
    print(f"Loading data into '{table_name}'...")
    df.to_sql(table_name, con=engine, if_exists='append', index=False)
    print(f"Table '{table_name}' created and data loaded successfully.")

if __name__ == "__main__":
    ddl_final_features = """ CREATE TABLE public.final_features (
        "timestamp" timestamptz NULL,
        icao24 text NULL,
        callsign text NULL,
        airline text NULL,
        country text NULL,
        "date" timestamp NULL,
        "hour" timestamptz NULL,
        monthday int8 NULL,
        weekday int8 NULL,
        day_period text NULL,
        "month" int8 NULL,
        season text NULL,
        calendar text NULL,
        is_night bool NULL,
        is_holiday bool NULL,
        is_high_traffic bool NULL,
        runway int8 NULL,
        runway_config int8 NULL,
        runway_changed bool NULL,
        landings_since_change int8 NULL,
        wind_dir int8 NULL,
        wind_direction_category text NULL,
        wind_speed int8 NULL,
        wind_speed_category text NULL,
        is_wind_vrb bool NULL,
        varying_spread float8 NULL,
        varying_wind_from float8 NULL,
        varying_wind_to float8 NULL,
        is_wind_gusty bool NULL,
        gust_factor float8 NULL,
        gust_delta float8 NULL,
        is_wind_vardaris bool NULL,
        is_wind_sea_breeze bool NULL,
        headwind_10 float8 NULL,
        crosswind_10 float8 NULL,
        headwind_28 float8 NULL,
        crosswind_28 float8 NULL,
        headwind_16 float8 NULL,
        crosswind_16 float8 NULL,
        headwind_34 float8 NULL,
        crosswind_34 float8 NULL,
        weather_intensity text NULL,
        weather_category text NULL,
        temperature int8 NULL,
        temperature_category text NULL,
        dew_point int8 NULL,
        visibility int8 NULL,
        visibility_category text NULL,
        pressure int8 NULL,
        pressure_category text NULL,
        min_clouds_height float8 NULL,
        clouds_layers int8 NULL,
        is_ceiling bool NULL,
        ceiling_height float8 NULL,
        ceiling_category text NULL,
        is_convective bool NULL,
        convective_height float8 NULL,
        manufacturer text NULL,
        models text NULL,
        engine float8 NULL,
        engine_type text NULL,
        wtc text NULL
    );"""

    ddl_final_features_extended = """ CREATE TABLE public.final_features_extended (
        "timestamp" timestamptz NULL,
        icao24 text NULL,
        callsign text NULL,
        airline text NULL,
        country text NULL,
        runway int8 NULL,
        "date" timestamp NULL,
        "hour" timestamptz NULL,
        latitude float8 NULL,
        longitude float8 NULL,
        groundspeed float8 NULL,
        vertical_rate float8 NULL,
        onground bool NULL,
        alert bool NULL,
        altitude float8 NULL,
        geoaltitude float8 NULL,
        monthday int8 NULL,
        weekday int8 NULL,
        day_period text NULL,
        "month" int8 NULL,
        season text NULL,
        calendar text NULL,
        is_night bool NULL,
        is_holiday bool NULL,
        is_high_traffic bool NULL,
        runway_config int8 NULL,
        runway_changed bool NULL,
        landings_since_change int8 NULL,
        wind_dir int8 NULL,
        wind_direction_category text NULL,
        wind_speed int8 NULL,
        wind_speed_category text NULL,
        is_wind_vrb bool NULL,
        varying_spread float8 NULL,
        varying_wind_from float8 NULL,
        varying_wind_to float8 NULL,
        is_wind_gusty bool NULL,
        gust_factor float8 NULL,
        gust_delta float8 NULL,
        wind_is_vardaris bool NULL,
        wind_is_sea_breeze bool NULL,
        headwind_10 float8 NULL,
        crosswind_10 float8 NULL,
        headwind_28 float8 NULL,
        crosswind_28 float8 NULL,
        headwind_16 float8 NULL,
        crosswind_16 float8 NULL,
        headwind_34 float8 NULL,
        crosswind_34 float8 NULL,
        weather_intensity text NULL,
        weather_category text NULL,
        temperature int8 NULL,
        temperature_category text NULL,
        dew_point int8 NULL,
        visibility int8 NULL,
        visibility_category text NULL,
        pressure int8 NULL,
        pressure_category text NULL,
        min_clouds_height float8 NULL,
        clouds_layers int8 NULL,
        is_ceiling bool NULL,
        ceiling_height float8 NULL,
        ceiling_category text NULL,
        is_convective bool NULL,
        convective_height float8 NULL,
        manufacturer text NULL,
        models text NULL,
        engine float8 NULL,
        engine_type text NULL,
        wtc text NULL
    );"""

    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Run for the first dataset
    create_table_with_ddl(
        "final_features", 
        ddl_final_features, 
        pd.read_csv("data/output/final_features.csv")
    )
    
    # Run for the extended dataset
    create_table_with_ddl(
        "final_features_extended", 
        ddl_final_features_extended, 
        pd.read_csv("data/output/final_features_extended.csv")
    )