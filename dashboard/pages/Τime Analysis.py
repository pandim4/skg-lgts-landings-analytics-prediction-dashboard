import os
import streamlit as st
import pandas as pd
import sqlalchemy
import plotly.express as px
import calendar

from dotenv import load_dotenv
from functions import filters,setup_page

load_dotenv()
engine = sqlalchemy.create_engine(os.getenv('DB_URL'))

@st.cache_data
def get_processed_data():
    df = pd.read_sql("SELECT * FROM final_features", engine)
    geo_df = pd.read_sql("SELECT timestamp,date,callsign,latitude,longitude,groundspeed,altitude,vertical_rate FROM final_features_extended", engine)
    return df, geo_df

setup_page(category="Time", page_title="⏰ Time Analysis")

df, geo_df = get_processed_data()
df = filters(df)

m = st.container()
m1, m2, m3, m4, m5, m6 = st.columns(6)

df['date'] = df['date'].dt.date
df['hour'] = df['hour'].dt.tz_convert('Europe/Athens').dt.hour

monthly_rate = df.groupby('month').agg(total_landings=('date', 'count'), unique_days=('date', 'nunique'))
monthly_rate['daily_rate'] = monthly_rate['total_landings'] / monthly_rate['unique_days']
monthly_rate = monthly_rate.reset_index()

m.metric(label="Total Landings", value=f"{len(df)}")
m1.metric(label="Average Landings per Day", value=f"{len(df)/df['date'].nunique():.2f}")
m2.metric(label="Busiest Month", value=f"{calendar.month_name[df['month'].value_counts().idxmax()]}",delta=f"{(df['month'].value_counts().max())} landings")
m3.metric(label="Busiest Month by Daily Rate", value=f"{calendar.month_name[monthly_rate['month'].iloc[monthly_rate['daily_rate'].idxmax()]]}",delta=f"{monthly_rate['daily_rate'].max():.2f} landings/day")
m4.metric(label="Busiest Day of Week", value=f"{calendar.day_name[df['weekday'].value_counts().idxmax()]}",delta=f"{(df['weekday'].value_counts().max())} landings")
m5.metric(label="Busiest Day", value=f"{df['date'].value_counts().idxmax()}",delta=f"{(df['date'].value_counts().max())} landings")
m6.metric(label="Busiest Hour (24h)", value=f"{df['hour'].value_counts().idxmax()}:00",delta=f"{(df['hour'].value_counts().max())} landings") 

def histogram_with_order(df, column_name, title, x_label, category_order):
    """
    Creates a customized Plotly histogram enforcing a predefined categorical 
    order across the x-axis (e.g., chronological days/months).

    Args:
        df (pd.DataFrame): The dataset.
        column_name (str): The feature column to plot.
        title (str): The main chart title.
        x_label (str): The x-axis display label.
        category_order (list): The strict list of values dictating axis layout.

    Returns:
        plotly.graph_objects.Figure: The constructed Plotly figure.
    """
    fig = px.histogram(df, x=column_name, title=title, labels={column_name: x_label}, category_orders={column_name: category_order},color_discrete_sequence=['#1976D2'])
    fig.update_xaxes(tickmode='array', tickvals=category_order)
    fig.update_layout(bargap=0.1) 
    return fig

fig_monthly = histogram_with_order(df, 'month', "Monthly Distribution of Landings", "Month", list(range(1,13)))
fig_monthly.update_xaxes(ticktext=[calendar.month_abbr[i] for i in range(1,13)])
fig_weekday = histogram_with_order(df, 'weekday', "Distribution of Landings by Day of Week", "Day of Week", list(range(7)))
fig_weekday.update_xaxes(ticktext=[calendar.day_abbr[i] for i in range(7)])
fig_hourly = histogram_with_order(df, 'hour', "Hourly Distribution of Landings", "Hour of Day", list(range(24)))
fig_hourly.update_xaxes(ticktext=[f"{i}:00" for i in range(24)])

col1, col2, col3 = st.columns(3)
col1.plotly_chart(fig_monthly, use_container_width=True)
col2.plotly_chart(fig_weekday, use_container_width=True)
col3.plotly_chart(fig_hourly, use_container_width=True)

fig_rate = px.line(
    monthly_rate, 
    x='month', 
    y='daily_rate', 
    title="Average Daily Landings Rate per Month",
    labels={'month': 'Month', 'daily_rate': 'Average Daily Landings'},
    markers=True,
    line_shape="spline",
    color_discrete_sequence=['#1976D2']
)

fig_rate.update_xaxes(
    tickvals=list(range(1, 13)),
    ticktext=[calendar.month_abbr[i] for i in range(1, 13)]
)

st.plotly_chart(fig_rate, use_container_width=True)

st.divider()

df['runway_config'] = df['runway_config'].astype(str).str.strip()

runway_colors = {
    "16": "#1976D2", # Dark Blue
    "34": "#E53935", # Dark Red
    "10": "#43A047", # Dark Green
    "28": "#FFA000"  # Dark Orange
}

wind_direction_order = {"wind_direction_category": ["North", "Northeast", "East", "Southeast", "South", "Southwest", "West", "Northwest", "Variable"]}
day_period_order = ["Early Morning", "Morning", "Afternoon", "Evening", "Night"]

col1, col2 = st.columns(2)

with col1:
    st.subheader("Runway Configuration Selection by Time of Day")
    fig_time_runway = px.histogram(
            df,
            x="day_period",
            color="runway_config",
            color_discrete_map=runway_colors,
            category_orders={"day_period": day_period_order},
            barmode="group",
            title="Runway Configuration Selection by Time of Day",
            labels={'day_period': 'Time of Day', 'runway_config': 'Runway Configuration'}
        )
    st.plotly_chart(fig_time_runway, use_container_width=True)

with col2:
    st.subheader("Wind Direction by Time of Day")
    fig_time_wind = px.histogram(
            df,
            x="day_period",
            color="wind_direction_category",
            color_discrete_sequence=px.colors.qualitative.Set2,
            category_orders={"day_period": day_period_order, "wind_direction_category": wind_direction_order["wind_direction_category"]},
            barmode="group",
            title="Wind Direction Distribution by Time of Day",
            labels={'day_period': 'Time of Day', 'wind_direction_category': 'Wind Direction Category'}
        )
    st.plotly_chart(fig_time_wind, use_container_width=True)

st.subheader("Runway Configuration Selection by Time of Day and Season")

selected_season = st.selectbox("Select Season", options=df['season'].unique(), index=0)
selected_df = df[df['season'] == selected_season]

month_name_list = list(calendar.month_name)
selected_months = st.multiselect("Select Months", options=month_name_list[1:], default=month_name_list[1:])
filtered_df = selected_df[selected_df['month'].isin([month_name_list.index(month) for month in selected_months])]

fig_time_runway_season = px.histogram(
        filtered_df,
        x="day_period",
        color="runway_config",
        color_discrete_map=runway_colors,
        category_orders={"day_period": day_period_order},
        barmode="group",
        title="Runway Configuration Selection by Time of Day and Season",
        labels={'day_period': 'Time of Day', 'runway_config': 'Runway Configuration', 'season': 'Season', 'count': 'Number of Landings'}
    )
fig_time_runway_season.update_layout(legend_title_text='Runway Configuration')
st.plotly_chart(fig_time_runway_season, use_container_width=True)

st.subheader("Vardaris Vs Seabreeze by Time of Day")

col1, col2 = st.columns(2)

with col1:
    vardaris_df = df[df['is_wind_vardaris'] == True]
    fig_vardaris = px.histogram(
        vardaris_df,
        x="day_period",
        color="is_wind_vardaris",
        color_discrete_sequence=['#E53935', '#43A047'],
        category_orders={"day_period": day_period_order},
        barmode="group",
        title="Vardaris Distribution by Time of Day"
    )
    fig_vardaris.update_layout(xaxis_title="Time of Day", yaxis_title="Number of Landings", showlegend=False)
    st.plotly_chart(fig_vardaris, use_container_width=True)

with col2:
    seabreeze_df = df[df['is_wind_sea_breeze'] == True]
    fig_seabreeze = px.histogram(
        seabreeze_df,
        x="day_period",
        color="is_wind_sea_breeze",
        color_discrete_sequence=['#1976D2', '#FFA000'],
        category_orders={"day_period": day_period_order},
        barmode="group",
        title="Seabreeze Distribution by Time of Day",
    )
    fig_seabreeze.update_layout(xaxis_title="Time of Day", yaxis_title="Number of Landings", showlegend=False)
    st.plotly_chart(fig_seabreeze, use_container_width=True)

daily_rate = df.groupby(['date','is_holiday']).size().reset_index(name='daily_landings')
    
fig_holiday = px.box(
    daily_rate[daily_rate['daily_landings'] > 15], 
    x='is_holiday',
    y='daily_landings',
    title="Daily Landings Distribution on Holidays vs Non-Holidays",
    labels={'is_holiday': 'Is Holiday', 'daily_landings': 'Number of Landings'},
    color='is_holiday',
    color_discrete_sequence=['#1976D2', '#E53935']
)

fig_holiday.update_layout(
    showlegend=False,
    xaxis=dict(
        tickmode='array',
        tickvals=[0, 1],
        ticktext=['Holiday', 'Non-Holiday']
    ),
    yaxis=dict(
        range=[0, daily_rate['daily_landings'].max() + 5]
    )
)

st.plotly_chart(fig_holiday, use_container_width=True)

st.write(f"Average Daily Landings on Holidays: {daily_rate[daily_rate['is_holiday'] == 1]['daily_landings'].mean():.2f}")
st.write(f"Average Daily Landings on Non-Holidays: {daily_rate[daily_rate['is_holiday'] == 0]['daily_landings'].mean():.2f}")

daylight_rate = df.groupby(['date','is_night']).size().reset_index(name='daily_landings')

fig_daylight = px.box(
    daylight_rate,
    x='is_night',
    y='daily_landings',
    title="Distribution of Landings by Daylight vs Night",
    labels={'is_night': 'Is Night', 'daily_landings': 'Number of Landings'},
    color='is_night',
    color_discrete_sequence=['#1976D2', '#E53935']
)

fig_daylight.update_layout(
    showlegend=False,
    xaxis=dict(
        tickmode='array',
        tickvals=[0, 1],
        ticktext=['Daylight', 'Night']
    ),
    yaxis=dict(
        range=[0, daylight_rate['daily_landings'].max() + 5]
    )
)
st.plotly_chart(fig_daylight, use_container_width=True)

st.write(f"Average Daily Landings during Daylight: {daylight_rate[daylight_rate['is_night'] == 0]['daily_landings'].mean():.2f}")
st.write(f"Average Daily Landings during Night: {daylight_rate[daylight_rate['is_night'] == 1]['daily_landings'].mean():.2f}")