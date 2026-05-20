import numpy as np
import pandas as pd
from astral import LocationInfo
from astral.sun import sun
import holidays

gr_holidays = holidays.Greece(years=[2024])
city = LocationInfo(name="Thessaloniki", region="Greece", timezone="Europe/Athens", latitude=40.6401, longitude=22.9444)

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
    df['wind_gusts']=df['wind_gusts'].fillna(df['wind_speed'])
    df['gust_factor'] = df['wind_gusts'] / df['wind_speed'].replace(0, np.nan)
    df['gust_delta']= df['wind_gusts'] - df['wind_speed']
    df['is_wind_gusty']=(df['gust_factor'] > 1).astype(bool)

    df['is_wind_vrb']=(df['wind_dir'] == -1).astype(bool)
    df['varying_spread'] = (df['varying_wind_to'] - df['varying_wind_from']) % 360
    df['varying_spread'] = df['varying_spread'].fillna(0)

    vardaris_direction=340
    df['wind_is_vardaris'] = (abs((df['wind_dir'] - vardaris_direction + 180) % 360 - 180)<=30) & ((df['wind_speed']>=15) | (df['gust_factor']>1))

    sea_breeze_direction=180
    df['wind_is_sea_breeze'] = (abs((df['wind_dir'] - sea_breeze_direction + 180) % 360 - 180)<=30) & (df['wind_speed'].between(3, 15))

    def wind_speed_category(speed):
        if speed < 5: return "Calm"
        elif speed < 15: return "Light"
        elif speed < 25: return "Moderate"
        elif speed < 35: return "Strong"
        else: return "Very Strong"
    
    df['wind_speed_category'] = df['wind_speed'].apply(wind_speed_category)

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

    runways=[104,284,166,346]
    speed = df['wind_speed'].copy()
    direction = df['wind_dir'].copy()
    speed[df['is_wind_vrb']] = 0
    direction[df['is_wind_vrb']] = 0

    for runway in runways:
        radians=np.radians(direction-runway)
        df[f'headwind_{runway//10}']= speed * np.cos(radians)
        df[f'crosswind_{runway//10}']= speed * np.sin(radians)

def calculate_weather_phenomena(df):
    """
    Standardizes categorical representations of weather element intensity 
    and groups composite atmospheric descriptions into primary analytical bins.

    Args:
        df (pd.DataFrame): Weather observation dataframe dataset.

    Returns:
        None
    """
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
    df['weather_precipitation'].isna() & df['weather_descriptor'].isna() & df['weather_obscuration'].isna()
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
def ceiling_category(ceil):
    if ceil < 500: return 'LIFR'
    elif ceil < 1000: return 'IFR'
    elif ceil <= 3000:  return 'MVFR'
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
    height_columns=['cloud1_height', 'cloud2_height', 'cloud3_height']
    amount_columns=['cloud1_amount', 'cloud2_amount', 'cloud3_amount']
    formation_columns=['cloud1_formation', 'cloud2_formation', 'cloud3_formation']
    
    df['min_clouds_height'] = df[height_columns].min(axis=1)
    df['clouds_layers'] = df[height_columns].count(axis=1)

    ceiling_values=['BKN','OVC']
    temp_heights = df[height_columns].where(df[amount_columns].isin(ceiling_values).values)
    df['ceiling_height'] = temp_heights.min(axis=1)
    df['is_ceiling'] = df['ceiling_height'].notna()
    df['ceiling_category'] = df[['ceiling_height']].apply(lambda x: ceiling_category(x['ceiling_height']), axis=1)

    convective_values=['CB','TCU']
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

    weather_df = weather_df.drop(columns=['wind_gusts','weather_descriptor','weather_precipitation','weather_obscuration','cloud1_height', 'cloud2_height', 'cloud3_height','cloud1_amount', 'cloud2_amount', 'cloud3_amount','cloud1_formation', 'cloud2_formation', 'cloud3_formation'])

    timestamp=['timestamp']
    wind=['wind_dir','wind_direction_category','wind_speed','wind_speed_category','is_wind_vrb','varying_spread','varying_wind_from','varying_wind_to','is_wind_gusty','gust_factor','gust_delta','wind_is_vardaris','wind_is_sea_breeze','headwind_10','crosswind_10','headwind_28','crosswind_28','headwind_16','crosswind_16','headwind_34','crosswind_34']
    weather_phenomena=['weather_intensity','weather_category']
    other=['temperature','temperature_category','dew_point','visibility','visibility_category','pressure','pressure_category']
    clouds=['min_clouds_height','clouds_layers','is_ceiling','ceiling_height','ceiling_category','is_convective','convective_height']
    columns_order = timestamp + wind + weather_phenomena + other + clouds

    weather_df = weather_df.sort_values(by='timestamp')
    weather_df = weather_df.reindex(columns=columns_order)
    return weather_df

def is_night(fg):
    """Evaluates if an astronomical solar night phase is active for a given timestamp."""
    s = sun(city.observer, date=fg['timestamp'].date(), tzinfo=city.timezone)
    local_tz=fg['timestamp'].tz_convert('Europe/Athens')
    return (local_tz < s['sunrise']) or (local_tz > s['sunset'])

def calendar_season(month):
    """Maps numeric month representations into corresponding seasonal categories."""
    if month in {12, 1, 2}: return 'Winter'
    elif month in {3, 4, 5}: return 'Spring'
    elif month in {6, 7, 8}: return 'Summer'
    else: return 'Autumn'

def high_traffic(fg):
    """Identifies high traffic hours by checking if the traffic count exceeds the 80th percentile."""
    landings_per_hour=fg.groupby('hour').size()
    high_traffic_threshold=landings_per_hour.quantile(0.8)
    high_traffic_hours=landings_per_hour[landings_per_hour>=high_traffic_threshold].index
    return fg['hour'].isin(high_traffic_hours)

def runway_config(fg):
    """
    Tracks and identifies macro airport runway configuration layouts, detecting operational 
    changes and counting landing sequences since the last configuration update.

    Args:
        fg (pd.DataFrame): Chronological records dataset tracking landings.

    Returns:
        pd.DataFrame: The modified dataframe with configured historical sequences.
    """
    session_id = (fg['runway'] != fg['runway'].shift(1)).cumsum()
    counts = fg.groupby(session_id)['runway'].transform('count')
    
    fg['runway_config'] = fg['runway'].where(counts >= 3)
    fg['runway_config'] = fg['runway_config'].ffill().bfill()
    fg['runway_config'] = fg['runway_config'].astype(int)
    fg.loc[fg.index[0], 'runway_config'] = fg.loc[fg.index[0], 'runway']
    fg.loc[fg.index[len(fg)-1], 'runway_config'] = fg.loc[fg.index[len(fg)-1], 'runway']

    fg['runway_changed'] = fg['runway_config'] != fg['runway_config'].shift(1)
    fg.loc[fg.index[0], 'runway_changed'] = False

    session_id = (fg['runway_config'] != fg['runway_config'].shift(1)).cumsum()
    fg['landings_since_change'] = fg.groupby(session_id).cumcount() + 1
    return fg

def day_period(h):
    """Maps specific localized hour ranges into broad, analytical time-of-day categories."""
    local_hour = h.tz_convert('Europe/Athens').hour
    if 4 <= local_hour < 8: return "Early Morning"
    elif 8 <= local_hour < 12: return "Morning"
    elif 12 <= local_hour < 17: return "Afternoon"
    elif 17 <= local_hour < 21: return "Evening"
    else: return "Night"

def apply_time_features(landings_df):
    """
    Extracts time features from timestamps, maps seasonal fields, computes night states,
    and flags national holiday observations.

    Args:
        landings_df (pd.DataFrame): Core approach observations log.

    Returns:
        pd.DataFrame: Dataframe populated with structured time attributes.
    """
    landings_df['monthday']=landings_df['timestamp'].dt.day
    landings_df['weekday']=landings_df['timestamp'].dt.dayofweek
    landings_df['day_period'] = landings_df['hour'].apply(day_period)
    landings_df['month']=landings_df['timestamp'].dt.month
    landings_df['season'] = landings_df['month'].apply(calendar_season)
    landings_df['calendar'] = np.where((landings_df['timestamp'] < pd.Timestamp(2024, 3, 31,tz='UTC')) | (landings_df['timestamp'] > pd.Timestamp(2024, 10, 27,tz='UTC'))  , 'Winter', 'Summer')
    landings_df['is_night']= landings_df.apply(is_night, axis=1)
    landings_df['is_holiday'] = landings_df['timestamp'].dt.date.isin(gr_holidays)
    return landings_df

def apply_traffic_features(landings_df):
    """Calculates density metrics and compiles runway configuration attributes."""
    landings_df['is_high_traffic'] = high_traffic(landings_df)
    landings_df = runway_config(landings_df)
    return landings_df

def calculate_landing_features(landings_df):
    """
    Cleans duplicates, builds structural chronological markers, calculates airport traffic 
    features, and manages column schemas.

    Args:
        landings_df (pd.DataFrame): Base approach landing log entries.

    Returns:
        pd.DataFrame: Formatted dataframe tracking primary arrival metrics.
    """
    landings_df = landings_df.drop_duplicates(subset=['date', 'callsign'], keep='first').reset_index(drop=True)
    landings_df=apply_time_features(landings_df)
    landings_df=apply_traffic_features(landings_df)
    order=['timestamp','icao24','callsign','airline','country','date','hour','monthday','weekday','day_period','month','season','calendar','is_night','is_holiday','is_high_traffic','runway','runway_config','runway_changed','landings_since_change']
    landings_df = landings_df[order]
    return landings_df

def calculate_landing_features_extended(landings_df, landings_df2):
    """
    Merges analytical context indicators back into an extended telemetry frame tracking granular flight states.

    Args:
        landings_df (pd.DataFrame): Extracted core features summary file.
        landings_df2 (pd.DataFrame): Massive source file containing granular positional coordinate telemetry.

    Returns:
        pd.DataFrame: Expanded granular analytical logging table.
    """
    landings_df2=apply_time_features(landings_df2)
    traffic_cols = ['is_high_traffic','runway_config','runway_changed','landings_since_change']
    landings_df2 = landings_df2.merge(landings_df[['callsign', 'date'] + traffic_cols], on=['callsign', 'date'], how='left')
    return landings_df2

def calculate_aircraft_features(aircrafts_df):
    """
    Parses design text codes to separate mechanical engine features, categorizes propulsion models, 
    and translates wake turbulence category codes into meaningful text descriptors.

    Args:
        aircrafts_df (pd.DataFrame): Unformatted reference plane specifications data sheet.

    Returns:
        pd.DataFrame: Unified technical aircraft lookup sheet.
    """
    rule=r"(?:L)([1-8])(J|T|P|E|R)"
    aircrafts_df[['engine','engine_type']]=aircrafts_df['type'].str.extract(rule)
    aircrafts_df['engine'] = aircrafts_df['engine'].astype('Int8')

    engine_map={'J':'Jet','T':'Turboprop','P':'Piston','E':'Electric','R':'Rocket'}
    wtc_map={'L':'Light','M':'Medium','H':'Heavy'}

    aircrafts_df['engine_type'] = aircrafts_df['engine_type'].map(engine_map)
    aircrafts_df['wtc'] = aircrafts_df['wtc'].map(wtc_map)
    aircrafts_df = aircrafts_df.drop(columns=['type'])

    columns_order = ['icao24','manufacturer','models','engine','engine_type', 'wtc']
    aircrafts_df = aircrafts_df.reindex(columns=columns_order)
    return aircrafts_df

def merge_features(df_landings, df_weather, df_aircrafts, df_landings_extended):
    """
    Merges different feature spaces (landings, weather, and aircraft specs) together. 
    Uses an asof join to link each flight log entry with the closest weather report.

    Args:
        df_landings (pd.DataFrame): Computed arrivals metric framework table.
        df_weather (pd.DataFrame): Multi-property meteorological context dataset.
        df_aircrafts (pd.DataFrame): Technical airplane specs dataset.
        df_landings_extended (pd.DataFrame): Detailed trajectory parameters logs.

    Returns:
        tuple: (Combined consolidated master features DataFrame, Combined extended telemetry master features DataFrame)
    """
    landweath_df = pd.merge_asof(df_landings, df_weather, left_on='timestamp', right_on='timestamp', direction='nearest', tolerance=pd.Timedelta('1 hour'))
    landweath_df_extended = pd.merge_asof(df_landings_extended, df_weather, left_on='timestamp', right_on='timestamp', direction='nearest', tolerance=pd.Timedelta('1 hour'))

    final_df = pd.merge(landweath_df, df_aircrafts, on='icao24', how='left')
    final_df_extended = pd.merge(landweath_df_extended, df_aircrafts, on='icao24', how='left')

    return final_df, final_df_extended