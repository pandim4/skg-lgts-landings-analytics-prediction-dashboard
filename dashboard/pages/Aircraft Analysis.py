import os
import streamlit as st
import pandas as pd
import sqlalchemy
import plotly.express as px

from dotenv import load_dotenv
from functions import filters,setup_page
from config import model_colors, airline_colors, countries_colors, manufacturer_colors, day_period_order,category_order

load_dotenv()
engine = sqlalchemy.create_engine(os.getenv('DB_URL'))

@st.cache_data
def get_processed_data():
    df = pd.read_sql("SELECT * FROM final_features", engine)

    geo_df = pd.read_sql("SELECT timestamp,date,callsign,latitude,longitude,groundspeed,altitude,vertical_rate,onground,models,wtc,engine,manufacturer FROM final_features_extended", engine)

    return df, geo_df

setup_page(category="Aircraft", page_title="✈️ Aircraft Analysis")

df, geo_df = get_processed_data()

df = filters(df)

match_keys = df[['date', 'callsign']]
geo_df = geo_df.merge(match_keys, on=['date', 'callsign'], how='inner')

m = st.container()
m.metric(label="Total Landings", value=f"{len(df):,}")
st.divider()

st.subheader("Overview of Aircraft Utilization at SKG Airport")
mm1,mm2,mm3 = st.columns(3)
 
mm2.metric(label="Total Unique Callsigns/Flights", value=f"{df['callsign'].nunique():,}",delta=f"{(df['callsign'].nunique()/len(df)*100):.2f}% of total landings")
mm3.metric("Primary Airline", df['airline'].mode()[0],delta=f"{(df['airline'].value_counts().iloc[0]/len(df)*100):.2f}% of total landings")
st.divider()

st.subheader("Overview of Aircraft Diversity at SKG Airport")
m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Total Different Airlines", len(df['airline'].unique()))
m2.metric("Total Different Countries", len(df['country'].unique()))
m3.metric("Total Different Manufacturers", len(df['manufacturer'].unique()))
m4.metric("Total Different Models", len(df['models'].unique()))

st.divider()

st.subheader("Top 10 Airlines, Countries, Manufacturers & Models")

#Sort out the top 10 categories and group the rest as "Other" for better visualization
def get_top10_with_other(df, column_name):
    count_df = df[column_name].value_counts().reset_index()
    count_df.columns = [column_name, 'Flight Count']

    top10_df = count_df.head(10).copy()

    other_count = count_df['Flight Count'][10:].sum()
    other_row = pd.DataFrame({column_name: ['Other'], 'Flight Count': [other_count]})

    top10_df = pd.concat([top10_df, other_row], ignore_index=True)

    return top10_df

#Display a pie chart for the top 10 categories with the "Other" category included
def pie_chart_with_top10(df, column_name, title, color_map, legend_title):
    top10_df = get_top10_with_other(df, column_name)

    fig = px.pie(
        top10_df,
        values='Flight Count',
        names=column_name,
        title=title,
        template="plotly_dark",
        color=column_name,
        color_discrete_map=color_map,
        hole=0.4
    )
    
    fig.update_layout(legend_title=legend_title)

    st.plotly_chart(fig, use_container_width=True)

#Calculate and display a leaderboard with counts and percentages for a given column
def calculate_and_display_leaderboard(df, column_name,column_title):
    leaderboard_df = df[column_name].value_counts().reset_index()
    leaderboard_df.columns = [column_title, 'Total Flights']

    total_flights = leaderboard_df['Total Flights'].sum()
    leaderboard_df['Share (%)'] = (leaderboard_df['Total Flights'] / total_flights * 100).round(2)

    leaderboard_df.index = leaderboard_df.index + 1
    leaderboard_df.index.name = 'Rank'

    with st.expander(f"Click to see the full {column_title} leaderboard"):
        st.dataframe(
            leaderboard_df, 
            column_config={
                column_title: f"{column_title} Name",
                "Total Flights": st.column_config.NumberColumn("Flights", format="%d"),
                "Share (%)": st.column_config.ProgressColumn("Share", min_value=0, max_value=100, format="%.2f%%"),
            },
            use_container_width=True
        )

col_left, col_right = st.columns(2)

#Pie charts for Airlines and Countries with "Other" category
with col_left:

    top10_airlines = get_top10_with_other(df, 'airline')
    pie_chart_with_top10(df, 'airline', "Utilisation by Airline (Top 10)", airline_colors, "Airline")

with col_right:

    top10_countries = get_top10_with_other(df, 'country')
    pie_chart_with_top10(df, 'country', "Utilisation by Country of Origin (Top 10)", countries_colors, "Country")

# Leaderboards for Airlines and Countries
calculate_and_display_leaderboard(df, 'airline', 'Airlines')
calculate_and_display_leaderboard(df, 'country', 'Countries')

st.divider()

col_left, col_right = st.columns(2)

#Pie charts for Manufacturers and Models with "Other" category
with col_left:

    top10_manufacturers = get_top10_with_other(df, 'manufacturer')
    pie_chart_with_top10(df, 'manufacturer', "Utilisation by Manufacturer (Top 10)", manufacturer_colors, "Manufacturer")

with col_right:

    top10_models = get_top10_with_other(df, 'models')
    pie_chart_with_top10(df, 'models', "Utilisation by Aircraft Model (Top 10)", model_colors, "Aircraft Model")

# Leaderboards for Manufacturers and Models
calculate_and_display_leaderboard(df, 'manufacturer', 'Manufacturers')
calculate_and_display_leaderboard(df, 'models', 'Aircraft Models')

st.divider()

st.subheader("Airline Fleet Composition (Top 10 Airlines & Models)")


airlines_fleet = df.groupby(['airline', 'models']).size().reset_index(name='Flight Count')
airlines_fleet = airlines_fleet[airlines_fleet['airline'].isin(top10_airlines['airline']) & airlines_fleet['models'].isin(top10_models['models'])]

fig_fleet = px.bar(
    airlines_fleet, 
    x="Flight Count", 
    y="airline", 
    color="models", 
    title="Fleet Composition: Which models each airline uses",
    color_discrete_map=model_colors,
    template="plotly_dark",
    barmode="stack", 
    text_auto='.2s'
)

fig_fleet.update_layout(
    xaxis_title="Number of Flights",
    yaxis_title="Airline",
    yaxis={'categoryorder':'total ascending'},
    legend_title="Aircraft Model",
    uniformtext_minsize=8, 
    uniformtext_mode='hide'
)

st.plotly_chart(fig_fleet, use_container_width=True)

st.divider()

st.subheader("Number of Flights by Airline per Time")

def plot_flight_distribution_by_time(df, top10_airlines,time_column, time_order, airline_colors,time_title):

    fig_time_airline = px.histogram(
    top10_airlines.merge(df[time_column], left_on='airline', right_on=df['airline']),
    x=time_column,
    color="airline",
    color_discrete_map=airline_colors,
    category_orders={time_column: time_order, "airline": top10_airlines['airline'].tolist()},
    barmode="group",
    title=f"Flight Distribution by Airline and {time_title}",
)
    fig_time_airline.update_layout(
    legend_title_text='Airline',
    xaxis_title=time_title,
    yaxis_title="Number of Flights"
)
    st.plotly_chart(fig_time_airline, use_container_width=True)


plot_flight_distribution_by_time(df, top10_airlines,'day_period', day_period_order, airline_colors,"Time of Day")
plot_flight_distribution_by_time(df, top10_airlines,'season', ['Winter', 'Spring', 'Summer', 'Autumn'], airline_colors,"Season")
plot_flight_distribution_by_time(df, top10_airlines,'weekday', ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'], airline_colors,"Day of the Week")
plot_flight_distribution_by_time(df, top10_airlines,'is_high_traffic', [True, False], airline_colors,"High Traffic Hours")



st.subheader("Daily Visits from the same Aircraft at SKG Airport (Top 10 Airlines)")

aircraft_rotation_df = df.groupby(['date', 'airline', 'icao24']).size().reset_index(name='Daily_Flights_per_Aircraft')
avg_rotation = aircraft_rotation_df.groupby('airline')['Daily_Flights_per_Aircraft'].mean().reset_index()
avg_rotation.columns = ['airline', 'avg_daily_flights_per_aircraft']
top_rotation_airline = avg_rotation.sort_values(by='avg_daily_flights_per_aircraft', ascending=False).iloc[0]
top_10_rot = avg_rotation.sort_values(by='avg_daily_flights_per_aircraft', ascending=False).head(10)

# Metrics
c1, c2 = st.columns(2)
c1.metric("Max Avg Daily Landings", f"{top_rotation_airline['avg_daily_flights_per_aircraft']:.2f}")
c2.metric("Most Frequent Operator", top_rotation_airline['airline'])

fig_rot = px.bar(
    top_10_rot,
    x='avg_daily_flights_per_aircraft',
    y='airline',
    title="Top 10 Airlines by Daily Aircraft Landings (Frequency)",
    template="plotly_dark",
    color='airline',
    color_discrete_map=airline_colors,
    text_auto='.2f'
)

fig_rot.update_layout(
    xaxis_title="Average Landings Per Day",
    yaxis_title="Airline",
    yaxis={'categoryorder':'total ascending'},
    legend_title="Aircraft Model",
    uniformtext_minsize=8, 
    uniformtext_mode='hide'
)

st.plotly_chart(fig_rot, use_container_width=True)

st.divider()

st.subheader("Top 10 Aircrafts & Callsign Breakdown")


top10_icao_list = df['icao24'].value_counts().head(10).index.tolist()
df_top10 = df[df['icao24'].isin(top10_icao_list)].copy()

fig_aircrafts = px.bar(
    df_top10,
    y='icao24',
    color='callsign',     
    title="Top 10 Most Utilized Aircrafts by Callsign",
    template="plotly_dark",
   
)


fig_aircrafts.update_layout(
    yaxis={'categoryorder':'total ascending'}, 
    xaxis={'categoryorder':'total ascending'},
    yaxis_title="Aircraft ID",
    xaxis_title="Number of Flights",
    legend_title="Callsign",
    uniformtext_minsize=8, 
    uniformtext_mode='hide'
)

fig_aircrafts.update_traces(marker_line_width=0)

# Επειδή τα callsigns μπορεί να είναι πολλά, κρύβουμε το legend για να μη γεμίσει η οθόνη
fig_aircrafts.update_layout(showlegend=False)

st.plotly_chart(fig_aircrafts, use_container_width=True)

st.divider()

st.subheader("Aircraft Performance Analysis")

# Φιλτράρουμε για χαμηλό υψόμετρο (π.χ. κάτω από 2000 πόδια)
landing_df = geo_df[(geo_df['altitude'] < 2000) & (geo_df['onground'] == False) & (geo_df['groundspeed'] > 90) & (geo_df['wtc'].notnull()) & (geo_df['engine'].notnull())]
#landing_df = landing_df[landing_df['manufacturer'].isin(['AIRBUS', 'BOEING', 'ATR'])]

landing_df['engine'] = landing_df['engine'].astype(int)
landing_df['engine'] = landing_df['engine'].astype(str)

fig = px.scatter(landing_df, 
                 x="groundspeed", 
                 y="vertical_rate",
                 color="models",
                 facet_col="wtc",          # <--- Αυτό κάνει τη μαγεία
                 facet_col_wrap=2,
                 facet_row='engine',
                 height=900,
                 template="plotly_dark",
                 category_orders=category_order,
                 #hover_data=['callsign','airline'], # Η χώρα που προσθέσαμε πριν!
                 color_discrete_map=model_colors,
                 opacity=0.5,
                 title="Stable Approach Check: Vertical Rate vs Ground Speed",
                 labels={"vertical_rate": "Vertical Speed (fpm)", "ground_speed": "Ground Speed (kt)"})

# Προσθήκη γραμμής "ορίου" (π.χ. -1000 fpm θεωρείται συχνά το όριο για stable approach)
fig.add_hline(y=-1000, line_dash="dash", line_color="red", annotation_text="Limit for Stable Approach")
fig.update_layout(legend_title="Aircraft Model", xaxis_title="Ground Speed (kt)", yaxis_title="Vertical Speed (fpm)")

st.plotly_chart(fig)

avg_groundspeed = landing_df['groundspeed'].mean()
avg_groundspeed_per_model = landing_df.groupby('models')['groundspeed'].mean().reset_index()
avg_groundspeed_per_wtc_engine = landing_df.groupby(['wtc', 'engine'])['groundspeed'].mean().reset_index()


st.write(f"Average Ground Speed during Approach: {avg_groundspeed:.2f} kt")

with st.expander("See Average Ground Speed by Aircraft Model"):
    avg_groundspeed_per_model.index = avg_groundspeed_per_model.index + 1
    st.dataframe(avg_groundspeed_per_model,
    column_config={
            "models": "Aircraft Model",
            "groundspeed": st.column_config.NumberColumn("Avg Ground Speed (kt)", format="%.2f"),
        },
    use_container_width=True

    )


with st.expander("See Average Ground Speed by Wake Turbulence Category and Engines"):

    avg_groundspeed_per_wtc_engine = avg_groundspeed_per_wtc_engine.sort_values(by='groundspeed', ascending=False).reset_index(drop=True)
    avg_groundspeed_per_wtc_engine.index = avg_groundspeed_per_wtc_engine.index + 1
    st.dataframe(avg_groundspeed_per_wtc_engine,
    column_config={
            "wtc": "Wake Turbulence Category",
            "engine": "Engines",
            "groundspeed": st.column_config.NumberColumn("Avg Ground Speed (kt)", format="%.2f"),
        },

    use_container_width=True)


fig_density = px.density_heatmap(
    geo_df,
    x="groundspeed",
    y="altitude",
    nbinsx=50,
    nbinsy=50,
    color_continuous_scale="Viridis",
    title="Density of Ground Speed vs Altitude for All Flights",
    template="plotly_dark"
)
fig_density.update_layout(xaxis_title="Ground Speed (kt)", yaxis_title="Altitude (ft)")
st.plotly_chart(fig_density, use_container_width=True)


# 1. Κρατάμε τα Top 12 μοντέλα (για να μην έχουμε άπειρες στήλες)
box_df = landing_df[landing_df['manufacturer'].isin(['AIRBUS', 'BOEING', 'ATR'])].copy()

# 3. Δημιουργία του Box Plot
fig_box = px.box(
    box_df, 
    x="models", 
    y="groundspeed", 
    color="manufacturer",
    color_discrete_map=manufacturer_colors,
    # facet_col="manufacturer", # ΠΡΟΑΙΡΕΤΙΚΑ: Αν θέλεις να σπάσουν σε 3 στήλες
    title="Speed Distribution Grouped by Manufacturer",
    points=False, 
    notched=True,
    template="plotly_dark",
)


fig_box.update_layout(xaxis={'categoryorder':'total descending'},xaxis_title="Aircraft Model", yaxis_title="Ground Speed (kt)", legend_title="Manufacturer")
st.plotly_chart(fig_box, use_container_width=True)






