import pandas as pd
from traffic.core import Traffic
from sklearn.cluster import DBSCAN
from sqlalchemy import create_engine, text
from database import create_table_in_database, get_data_from_database

def data_reduction(data):
    """
    Downsamples the flight trajectory traffic data to 5-second intervals and 
    cleans invalid structural entries using the traffic library ecosystem.

    Args:
        data (Traffic): A traffic library object enclosing trajectory data.

    Returns:
        None
    """
    t_reduced=data.resample("5s").eval()
    t_reduced=t_reduced.clean_invalid()
    t_reduced.to_parquet("data/output/landing_data_reduced_5s.parquet")

def handle_missing_values(data):
    """
    Fills missing values in squawk via forward/backward filling, interpolates 
    telemetry gaps linearly, and drops rows that remain completely invalid.

    Args:
        data (pd.DataFrame): The raw dataframe containing trajectory data.

    Returns:
        None
    """
    df_cleaned = data.assign(squawk=lambda x: x.groupby(['callsign','date'])['squawk'].transform(lambda g: g.ffill().bfill()))

    nan_columns=['groundspeed','track','vertical_rate','altitude','geoaltitude']
    df_cleaned[nan_columns] = df_cleaned.groupby(['callsign','date'])[nan_columns].transform(lambda x: x.interpolate(method='linear', limit=3))

    nan_important_columns=['groundspeed','track','vertical_rate','altitude']
    df_cleaned=df_cleaned.dropna(subset=nan_important_columns)
    df_cleaned.to_parquet("data/output/landing_data_null_cleaned.parquet")

def outliers_remover(fg):
    """
    Filtering predicate function to validate physical limits of flight properties 
    and verify a baseline sequence duration length.

    Args:
        fg (pd.DataFrame): A grouped slice of flight telemetry records.

    Returns:
        bool: True if the flight passes physical constraints, False otherwise.
    """
    altitude=fg['altitude'].between(-500,40000).all()
    groundspeed=fg['groundspeed'].between(0,450).all()
    vertical_rate=fg['vertical_rate'].between(-3000,1500).all()
    length = len(fg)>4
    return altitude and groundspeed and vertical_rate and length

def hampel(fg):
    """
    Applies an adaptive rolling median Hampel filter structure to clear spike 
    outliers across kinematic and locational attribute columns.

    Args:
        fg (pd.DataFrame): A grouped dataframe representation of a single flight path.

    Returns:
        pd.DataFrame: The smoothed dataframe with outlier values replaced by rolling medians.
    """
    required_diff = {
        'latitude': 0.01,        
        'longitude': 0.01,
        'altitude': 100,         
        'groundspeed': 40,      
        'vertical_rate': 500 
    }
    columns_to_smooth = ['latitude', 'longitude', 'altitude', 'groundspeed', 'vertical_rate']

    for column in columns_to_smooth:
        rolling_median = fg[column].rolling(window=5, center=True, min_periods=1).median()
        actual_diff = (fg[column] - rolling_median).abs()
        outliers = actual_diff > required_diff.get(column, 0)
        fg.loc[outliers, column] = rolling_median[outliers]
    return fg

def dbscan(fg):
    """
    Uses spatial 3D DBSCAN clustering (Latitude, Longitude, Altitude) to identify 
    and purge noisy outlier coordinates from the positional dataframe.

    Args:
        fg (pd.DataFrame): The input spatial trajectory data.

    Returns:
        pd.DataFrame: Dataframe containing only valid core cluster components.
    """
    X = fg[['latitude','longitude','altitude']].values
    dbscaned = DBSCAN(eps=0.01, min_samples=30).fit(X)
    fg['cluster'] = dbscaned.labels_
    fg = fg[fg['cluster'] != -1]
    return fg

def landing_classifier(fg):
    """
    Classifies if a flight log indicates a genuine final approach landing sequence 
    by checking speed, altitude ceilings, descent flags, and runway heading alignments.

    Args:
        fg (pd.DataFrame): Telemetry records representing a single flight block.

    Returns:
        bool: True if identified as a landing sequence, False otherwise.
    """
    overspeed =  (fg['groundspeed'] > 190).any()
    overflight = (fg['altitude'] > 2500).any()
    ascending = ((fg['vertical_rate'] > 0).sum() > 3)

    runways=[104,284,166,346]
    heading = fg.loc[(fg['groundspeed'] > 100) & (fg['onground'] != 1), 'track'].tail(10).mean()
    runway_aligned=any(abs((heading - runway + 180) % 360 - 180)<=5 for runway in runways)
    
    return not (overflight or ascending or overspeed) and runway_aligned

def data_cleaning(data):
    """
    Sequentially runs logical cleaning predicates, Hampel smoothing filters, 
    DBSCAN spatial clustering, and the landing approach filter classification.

    Args:
        data (pd.DataFrame): Raw trajectory dataframe data input.

    Returns:
        None
    """
    df_logical_cleaned=data.groupby(['callsign', 'date']).filter(outliers_remover)
    df_logical_cleaned=df_logical_cleaned.groupby(['callsign', 'date'], group_keys=False).apply(hampel)
    df_logical_cleaned=dbscan(df_logical_cleaned)

    logical_cleaned_t =Traffic(df_logical_cleaned)
    logical_cleaned_t.data["timestamp"] = pd.to_datetime(logical_cleaned_t.data["timestamp"])
    logical_cleaned_t=logical_cleaned_t.resample("5s").eval()
    df_logical_cleaned=logical_cleaned_t.data

    df_logical_cleaned= df_logical_cleaned.groupby(['callsign', 'date']).filter(landing_classifier)

    logical_cleaned_t =Traffic(df_logical_cleaned)
    df_logical_cleaned=df_logical_cleaned.sort_values('timestamp')
    df_logical_cleaned.to_parquet("data/output/landing_data_cleaned.parquet")

def remove_helicopters(data, raw_aircrafts_df):
    """
    Removes aircraft registry records classified as helicopters based on type class indicators.

    Args:
        data (pd.DataFrame): The flights dataframe table.
        raw_aircrafts_df (pd.DataFrame): The reference lookup table containing aircraft specifications.

    Returns:
        None
    """
    helicopters_mask = raw_aircrafts_df['icaoaircraftclass'].fillna('').str.startswith('H')
    helicopters = set(raw_aircrafts_df.loc[helicopters_mask, 'icao24'])

    df_final = data[~data['icao24'].isin(helicopters)]
    df_final=df_final.sort_values('timestamp')
    df_final.reset_index(drop=True).to_parquet("data/output/landing_data_final.parquet")

def find_runway(fg):
    """
    Determines the specific runway ID a flight path uses based on final track headings.

    Args:
        fg (pd.DataFrame): Grouped flight segment tracking dataframe records.

    Returns:
        pd.DataFrame: The updated dataframe containing a computed 'runway' column.
    """
    runways=[104,284,166,346]
    heading = fg.loc[fg['groundspeed'] > 100, 'track'].tail(10).mean()
    for runway in runways:
        if (abs((heading - runway + 180) % 360 - 180)<=5):
            fg['runway']=int(runway/10)
            break
    return fg

def set_types_and_add_runway_column(df):
    """
    Drops internal temporary pipeline columns, formats analytical data types 
    (categories, bools, numeric downsizes), and calculates runway mapping properties.

    Args:
        df (pd.DataFrame): Cleaned trajectory dataframe dataset.

    Returns:
        pd.DataFrame: Formatted dataframe with proper types and assigned runway IDs.
    """
    datetime_columns=['timestamp','date','hour']
    category_columns=['icao24','callsign','serials']
    boolean_columns=['onground', 'alert', 'spi']
    float_columns=['latitude', 'longitude', 'groundspeed', 'track', 
                'vertical_rate', 'altitude', 'geoaltitude','track_unwrapped','lastcontact']

    df = df.drop(columns=['cluster'])
    df = df.sort_values('timestamp')
    df.reset_index(drop=True, inplace=True)
    df['id'] = df.index
    df['local_id'] = df.groupby(['callsign', 'date']).cumcount()
    df.insert(0, 'id', df.pop('id'))
    df.insert(1, 'local_id', df.pop('local_id'))
    df = df.groupby(['callsign', 'date'], group_keys=False).apply(find_runway, include_groups=True)

    for column in datetime_columns:
        df[column]=pd.to_datetime(df[column])

    df[category_columns] = df[category_columns].astype('category')
    df[boolean_columns] = df[boolean_columns].astype('bool')
    df['squawk'] = df['squawk'].astype('Int64')
    df['runway'] = pd.to_numeric(df['runway'], downcast='integer')
    df[float_columns] = df[float_columns].astype('float32')

    df = df.groupby(['callsign', 'date'], group_keys=False).apply(find_runway, include_groups=True)
    return df
    
def apply_preprocessing_pipeline_landings(data, raw_aircrafts_df):
    """
    Executes the comprehensive data preparation framework pipeline for landing observations.

    Args:
        data (pd.DataFrame): Raw uncleaned trajectory dataframe logs.
        raw_aircrafts_df (pd.DataFrame): Master descriptive specifications file for planes.

    Returns:
        pd.DataFrame: Fully validated, type-mapped, and processed trajectories dataframe.
    """
    data['timestamp'] = pd.to_datetime(data['timestamp'])
    data['date'] = data['timestamp'].dt.date

    t = Traffic(data)
    data_reduction(t)
    df_reduced = pd.read_parquet("data/output/landing_data_reduced_5s.parquet")
    handle_missing_values(df_reduced)
    df_null_cleaned = pd.read_parquet("data/output/landing_data_null_cleaned.parquet")
    data_cleaning(df_null_cleaned)
    df_logical_cleaned = pd.read_parquet("data/output/landing_data_cleaned.parquet")
    remove_helicopters(df_logical_cleaned, raw_aircrafts_df)
    df_final = pd.read_parquet("data/output/landing_data_final.parquet")
    df_final = set_types_and_add_runway_column(df_final)

    return df_final

def apply_preprocessing_weather(df):
    """
    Orchestrates raw METAR ingestion strings decoding, maps proper temporal frames, 
    downcasts internal types, and formats weather output schemas.

    Args:
        df (pd.DataFrame): Dataframe storing unparsed raw METAR entry inputs.

    Returns:
        pd.DataFrame: Fully parsed weather data frame.
    """
    from metar import parse_multiple_metars
    df=parse_multiple_metars(df)
    df.to_csv("data/output/weather_data_parsed.csv", index=False)

    df = pd.read_csv("data/output/weather_data_parsed.csv")
    df['time']=pd.to_datetime(df['time'], utc=True)
    df['cavok_recorded'] = df['cavok_recorded'].fillna(False).infer_objects(copy=False).astype(bool)

    category_columns=df.select_dtypes(include="object").columns
    int_columns= df.select_dtypes(include="float64").columns

    df[category_columns]=df[category_columns].astype('category')
    df[int_columns]=df[int_columns].astype('Int64')

    df.sort_values('time', inplace=True)
    df.reset_index(drop=True, inplace=True)
    df['id'] = df.index
    df.insert(0, 'id', df.pop('id'))
    return df

def apply_preprocessing_aircrafts_airlines(aircrafts_data, airlines_data, flights_df):
    """
    Filters lookup datasets down exclusively to aircraft models and airline structures 
    present in the current historical flight registry slice.

    Args:
        aircrafts_data (pd.DataFrame): Complete global plane identifiers sheet.
        airlines_data (pd.DataFrame): Universal corporate commercial airlines reference registry.
        flights_df (pd.DataFrame): Active targeted processed landings dataset.

    Returns:
        tuple: (Filtered aircrafts DataFrame, Filtered airlines DataFrame)
    """
    unique_icaos = flights_df['icao24'].unique()
    unique_prefixes = flights_df['callsign'].str[:3].unique()

    aircrafts_df = aircrafts_data[aircrafts_data['icao24'].isin(unique_icaos)]
    airlines_df = airlines_data[airlines_data['icao'].isin(unique_prefixes)]

    return aircrafts_df, airlines_df