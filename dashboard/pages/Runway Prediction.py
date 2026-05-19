import os
import streamlit as st
import pandas as pd
import sqlalchemy

import requests
import calendar
from dotenv import load_dotenv
from functions import setup_page
from ml_functions import apply_time_features,calculate_weather_features,metar_parser,create_model,runway_prediction,data_ml_conversion,get_metar_forecast_df,get_metar_data

load_dotenv()
engine = sqlalchemy.create_engine(os.getenv('DB_URL'))

setup_page(category="Machine Learning", page_title="🤖 Machine Learning")
st.subheader("Runway configuration prediction based on time and weather features.")

st.divider()

#Calling the function to get the latest METAR data
raw_metar, raw_metar_df = get_metar_data()

# Function to prepare the data for machine learning prediction
def prepare_ml_data(raw_metar_df,time=pd.Timestamp.now().tz_localize('UTC')):

    # Create a DataFrame for time features
    time_df = pd.DataFrame({
        "timestamp": [time],
        "hour": [time.floor('H')]
    })
    # Apply time feature engineering to the time DataFrame
    time_df = apply_time_features(time_df)

    # Apply METAR parsing and weather feature engineering to the raw METAR DataFrame
    raw_metar_df=metar_parser(raw_metar_df)
    weather_df=calculate_weather_features(raw_metar_df)

   # Combine weather and time features into a single DataFrame
    final_df = pd.concat([weather_df, time_df], axis=1)

    # Remove duplicate columns if any and drop the original timestamp column
    final_df = final_df.loc[:, ~final_df.columns.duplicated()]
    final_df = final_df.drop(columns=['timestamp'])

    #Convert the final DataFrame into a format suitable for machine learning prediction
    ml_ready_df = data_ml_conversion(final_df)

    #Select only the features that are required for the model prediction
    currentX = ml_ready_df[model_features]

    return currentX,weather_df,time_df

# Create the machine learning model pipeline and get the list of features used by the model
model_pipeline,model_features = create_model()

#Predict the current runway configuration using the latest METAR data and the machine learning model
currentX,current_weather_df,current_time_df = prepare_ml_data(raw_metar_df)
current_predicted_runway = runway_prediction(currentX,model_pipeline)

#Call the function to get the forecasted METAR
metar_forecast_df = get_metar_forecast_df()

#Make predictions for the next 12 hours and 24 hours using the forecasted METAR data and the machine learning model
predictions = []
for i in range(len(metar_forecast_df)-1):
    futureX,future_weather_df,future_time_df = prepare_ml_data(raw_metar_df=pd.DataFrame({'metar': [metar_forecast_df.iloc[i]['metar']]}), time=pd.Timestamp.now().tz_localize('UTC') + pd.Timedelta(hours=i))
    predicted_runway = runway_prediction(futureX,model_pipeline)
    predictions.append(predicted_runway[0])

futureX,future_weather_df,future_time_df = prepare_ml_data(raw_metar_df=pd.DataFrame({'metar': [metar_forecast_df.iloc[6]['metar']]}), time=pd.Timestamp.now().tz_localize('UTC') + pd.Timedelta(hours=24))
predicted_runway = runway_prediction(futureX,model_pipeline)
predictions.append(predicted_runway[0])

column1,column2= st.columns(2,vertical_alignment="center")

with column1:

    m = st.container()
    m.metric(label="Current Predicted Runway Configuration", value=f"{current_predicted_runway[0]}")

with column2:

    st.image(
        f"gifs/{current_predicted_runway[0]}.gif"
    , 
    use_container_width=True
    )

st.divider()

pred0, pred1, pred2, pred3, pred4, pred5, pred6 = st.columns(7,vertical_alignment="center")

for i, pred in enumerate([pred0, pred1, pred2, pred3, pred4, pred5, pred6]):
    with pred:
        m = st.container()
        if i < len(predictions)-1:
            #m.metric(label=f"Predicted Runway in {(i+1)*2}h", value=f"{predictions[i]}")
            m.metric(label=f"Predicted Runway\n {(pd.Timestamp.now(tz='UTC').floor('h') + pd.Timedelta(hours=(i+1)*2)).tz_convert('Europe/Athens').strftime('%H:%M')}", value=f"{predictions[i]}")
        else:
            m.metric(label=f"Predicted Runway in {24}h", value=f"{predictions[i]}")
        st.image(
            f"gifs/{predictions[i]}.gif"
        , 
        use_container_width=True
        )

i = 0
while current_predicted_runway==predictions[i] and i < len(predictions)-1:
    i+=1

if i < len(predictions)-1:
    if i == 0:
        st.warning(
            f"**The runway configuration is expected to change within the next 2 hours.** "
            f"\n\n*(Estimated Change: {(pd.Timestamp.now(tz='UTC').floor('h') + pd.Timedelta(hours=2)).tz_convert('Europe/Athens').strftime('%H:%M')} Greece Time)*"
        )
    else:
        st.warning(
            f"**The runway configuration is expected to change in approximately {((i+1)*2)} hours.** "
            f"\n\n*(Estimated Change: {(pd.Timestamp.now(tz='UTC').floor('h') + pd.Timedelta(hours=(i+1)*2)).tz_convert('Europe/Athens').strftime('%H:%M')} Greece Time)*"
        )
else:
    st.warning(f"**The runway configuration is expected to remain the same for the next 12 hours.**")

st.divider()

col1, col2 = st.columns(2)

with col2:
    
    st.subheader("Current Weather Conditions")
    st.write(f"**Temperature:** {current_weather_df['temperature'][0]} °C")
    st.write(f"**Weather Phenomena:** {current_weather_df['weather_category'][0]}")
    st.write(f"**Wind Speed:** {current_weather_df['wind_speed'][0]} kt")
    st.write(f"**Wind Direction:** {current_weather_df['wind_dir'][0]}°" if current_weather_df['wind_dir'][0] != -1 else "**Wind Direction:** Variable")
    st.write(f"**Visibility:** {current_weather_df['visibility'][0]} m")
    st.write(f"**Landing Type:** {current_weather_df['ceiling_category'][0]}")


with col1:
    st.subheader("Current Time at SKG/LGTS")

    st.write(f"**UTC Time:** {current_time_df['timestamp'][0]}")
    st.write(f"**Local Time:** {current_time_df['timestamp'][0].tz_convert('Europe/Athens')}")
    st.write(f"**Time of Day:** {current_time_df['day_period'][0]}")
    st.write(f"**Hour of Day:** {current_time_df['hour'][0].tz_convert('Europe/Athens').hour}:00")

    st.write(f"**Day of Week:** {current_time_df['weekday'][0]} ({calendar.day_name[current_time_df['weekday'][0]]})")
    st.write(f"**Day of Month:** {current_time_df['monthday'][0]}")
    st.write(f"**Month:** {current_time_df['month'][0]} ({calendar.month_name[current_time_df['month'][0]]})")

    st.write(f"**Season:** {current_time_df['season'][0]}")
    st.write(f"**Calendar Period:** {current_time_df['calendar'][0]}")

    st.write(f"**Is it currently night?** {'Yes' if current_time_df['is_night'][0] else 'No'}")
    st.write(f"**Is it currently a holiday?** {'Yes' if current_time_df['is_holiday'][0] else 'No'}")

st.divider()
st.write(f"Current raw METAR: {raw_metar}")

st.write(f"Forecasted METARs for the next 12 hours:")
for i in range(len(metar_forecast_df)-1 ):
    st.write(f"- {metar_forecast_df.iloc[i][['metar','time']].to_dict()}")