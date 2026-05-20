from datetime import datetime, timedelta
from traffic.data import opensky
import pandas as pd
import os

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

##########

# Set parameters.
airport = "LGTS" # Set airport.
THbounds = (22.910248, 40.476592, 23.028740, 40.566666) # Set the geographical bounds of the area.

# the last date that was found (start dates for each quarter)
end_dates = [datetime(2023,12,31,23,59,59), datetime(2024,3,31,23,59,59), datetime(2024,6,30,23,59,59), datetime(2024,9,30,23,59,59)]
# the last date that will be checked now (end dates for each quarter)
end_points = [datetime(2024,3,31,23,59,59), datetime(2024,6,30,23,59,59), datetime(2024,9,30,23,59,59), datetime(2024,12,31,23,59,59)]


os.chdir(os.path.dirname(os.path.abspath(__file__)))

print("Welcome to the landings data mining and preparation script!")
print("You can change the parameters for the airport, geographical bounds, and date ranges in the code if needed.")
print("Currently set parameters:")
print(f"Airport: {airport}")
print(f"Geographical bounds: {THbounds}")
print(f"End dates: {end_points}")
print ("Use the landings data that have already been mined ?")
print ("Enter 'yes' to use existing data or 'no' to mine new data:")
read_input = input().strip().lower()
if read_input == 'yes':
    print("Using existing mined data. Skipping mining process.")
    print("How many quarters of data do you want to concatenate ? (Enter a number between 1 and 4):")
    n = int(input().strip())
    quarter_concatenation(n)
    print(f"landings_data.csv file created by concatenating {n} quarter files.")
elif read_input == 'no':
    print("Starting the mining process. This may take some time depending on the date range.")
    for i in range(len(end_dates)):
        flights_data_mining(end_dates[i], end_points[i], airport, THbounds, i+1)