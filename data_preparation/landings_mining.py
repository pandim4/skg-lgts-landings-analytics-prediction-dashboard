from datetime import datetime, timedelta
from traffic.data import opensky
import pandas as pd

def flights_data_mining(end_date, end_point, airport, THbounds, quarter_num):
    """
    Mines landing flight traffic historical data for a specific airport within 
    geographical boundaries from OpenSky Network, in 2-day chunks.

    Args:
        end_date (datetime): The starting date for mining (exclusive of previous data).
        end_point (datetime): The final end date/time for the data mining process.
        airport (str): The ICAO code of the target arrival airport (e.g., 'LGTS').
        THbounds (tuple): A tuple containing the bounding box coordinates (min_lon, min_lat, max_lon, max_lat).
        quarter_num (int): The identifier number of the quarter being processed, used for the output filename.

    Returns:
        None
    """
    data = {}
    i = 0

    while(end_date + timedelta(days=2, seconds=-1) < end_point):
        try: 
            start_date = end_date + timedelta(seconds=1)
            end_date = start_date + timedelta(days=2, seconds=-1)

            start = start_date.strftime("%Y-%m-%d %H:%M:%S")
            end = end_date.strftime("%Y-%m-%d %H:%M:%S")

            res = opensky.history(start, end, arrival_airport=airport, bounds=THbounds)
            
            if res is not None:
                data[i] = res.data 
                print("success in", start_date, end_date)
            i += 1
        except Exception as e:
            i += 1 
            print("failure in", end_date, "Error:", e)

    try:
        start_date = end_date + timedelta(seconds=1)
        end_date_final = end_point
        start = start_date.strftime("%Y-%m-%d %H:%M:%S")
        end = end_date_final.strftime("%Y-%m-%d %H:%M:%S")
        
        res = opensky.history(start, end, arrival_airport=airport, bounds=THbounds)
        
        if res is not None:
            data[i] = res.data
            print("success in", start_date, end_date_final)
    except Exception as e:
            print(f"failure in final segment. Error: {e}")

    if data:
        final_data = pd.concat(data.values(), ignore_index=True)
        final_data.to_csv(f"data/input/quarters_of_landings_data/quarter_{quarter_num}.csv", index=False)

def quarter_concatenation(n):
    """
    Concatenates multiple quarterly raw data CSV files into a single master CSV file.

    Args:
        n (int): The total number of quarterly files to read and combine.

    Returns:
        None
    """
    data={}
    for i in range (n):
        data[i]=pd.read_csv(f"data/input/quarters_of_landings_data/quarter_{i+1}.csv")

    df=pd.concat(data[i] for i in range (len(data)))
    df.to_csv("data/input/landings_data.csv", index=False)