import streamlit as st
import pandas as pd


# Filters

def make_multiselect_with_select_all(df, column_name, label):
    """
    Creates a Streamlit multiselect widget with a 'Select All' toggle option.

    Args:
        df (pd.DataFrame): The input dataframe.
        column_name (str): The column to filter on.
        label (str): The display label for the widget.

    Returns:
        pd.DataFrame: The filtered dataframe based on user selection.
    """
    st.sidebar.markdown(f"**{label}**")

    options = df[column_name].unique()
    if st.sidebar.checkbox(f"Select All {label}", value=True):
        selected_options = st.sidebar.multiselect(f"Select {label}(s)", options=options, default=options)
    else:
        selected_options = st.sidebar.multiselect(f"Select {label}(s)", options=options)
    
    if not selected_options:
        st.warning(f"Please select at least one {label.lower()} to display data.")
        st.stop()
    
    return df[df[column_name].isin(selected_options)]

def make_boolean_widget(df, column_name, label):
    """
    Creates a Streamlit checkbox widget for boolean filtering.

    Args:
        df (pd.DataFrame): The input dataframe.
        column_name (str): The boolean column to filter on.
        label (str): The display label for the checkbox.

    Returns:
        pd.DataFrame: The filtered dataframe if checked, else the original dataframe.
    """
    value = st.sidebar.checkbox(label, value=False)

    if value is True:
        return df[df[column_name] == True]
   
    return df


def make_slider_widget(df, column_name, label):
    """
    Creates a Streamlit slider widget for numerical range filtering.

    Args:
        df (pd.DataFrame): The input dataframe.
        column_name (str): The numerical column to filter on.
        label (str): The display label for the slider.

    Returns:
        pd.DataFrame: The filtered dataframe within the selected range.
    """
    min_val = df[column_name].min()
    max_val = df[column_name].max()
    selected_range = st.sidebar.slider(label, min_value=float(min_val), max_value=float(max_val), value=(float(min_val), float(max_val)))

    return df[(df[column_name] >= selected_range[0]) & (df[column_name] <= selected_range[1])]


def airline_filter(df):
    """Applies airline-specific filters to the dataframe via the sidebar."""
    df = make_multiselect_with_select_all(df, 'airline', 'Airlines')
    return df


def runway_filter(df):
    """Applies runway configuration and actual runway filters to the dataframe via the sidebar."""
    df = make_multiselect_with_select_all(df, 'runway_config', 'Runway Configurations')
    df = make_multiselect_with_select_all(df, 'runway', 'Actual Runways')
    return df

def wind_filter(df):
    """Applies categorical and numerical wind condition filters to the dataframe via the sidebar."""
    df = make_multiselect_with_select_all(df, 'wind_direction_category', 'Wind Direction Categories')
    df = make_slider_widget(df, 'wind_dir', 'Wind Direction Range')

    df = make_multiselect_with_select_all(df, 'wind_speed_category', 'Wind Speed Categories')
    df = make_slider_widget(df, 'wind_speed', 'Wind Speed Range')

    st.sidebar.markdown("**Wind Types**")
    df = make_boolean_widget(df, 'is_wind_gusty', 'Gusty Wind')
    df = make_boolean_widget(df, 'is_wind_vardaris', 'Vardaris Wind')
    df = make_boolean_widget(df, 'is_wind_sea_breeze', 'Sea Breeze Wind')

    return df


def time_filter(df):
    """Applies temporal and traffic condition filters to the dataframe via the sidebar."""
    df = make_multiselect_with_select_all(df, 'day_period', 'Time of Day')
    df = make_multiselect_with_select_all(df, 'season', 'Season')

    st.sidebar.markdown("**Traffic**")
    df = make_boolean_widget(df, 'is_high_traffic', 'High Traffic')
    df = make_boolean_widget(df, 'is_night', 'Nightfall')
    df = make_boolean_widget(df, 'is_holiday', 'Holiday')

    return df

def weather_filter(df):
    """Applies extensive meteorological filters (visibility, clouds, temperature, pressure) via the sidebar."""
    df = make_multiselect_with_select_all(df, 'visibility_category', 'Visibility Categories')
    df = make_multiselect_with_select_all(df, 'weather_intensity', 'Weather Intensities')
    df = make_multiselect_with_select_all(df, 'weather_category', 'Weather Categories')

    df = make_multiselect_with_select_all(df, 'ceiling_category', 'Approach Method Categories')
    df = make_multiselect_with_select_all(df, 'clouds_layers', 'Clouds Layers')
    df = make_boolean_widget(df, 'is_ceiling', 'Ceiling Clouds')
    df = make_boolean_widget(df, 'is_convective', 'Convective Clouds')

    df = make_multiselect_with_select_all(df, 'temperature_category', 'Temperature Categories')
    df = make_slider_widget(df, 'temperature', 'Temperature Range')

    df = make_multiselect_with_select_all(df, 'pressure_category', 'Pressure Categories')

    return df

def filters(df):
    """
    Orchestrates all sidebar filters and applies them sequentially to the dataset.

    Args:
        df (pd.DataFrame): The raw, unfiltered dataset.

    Returns:
        pd.DataFrame: The fully filtered dataset ready for visualization.
    """
    st.sidebar.header("Filters")
    df = airline_filter(df)
    df = runway_filter(df)
    df = wind_filter(df)
    df = time_filter(df)
    df = weather_filter(df)
    
    df = make_multiselect_with_select_all(df, 'wtc', 'WTC Categories')

    return df

def setup_page(category=None, page_title=None):
    """
    Configures the base Streamlit page layout, metadata, and dynamic title.

    Args:
        category (str, optional): The category of the dashboard page.
        page_title (str, optional): The specific title to display on the page.
    """
    title = f"SKG Dashboard - {category}" if category else "SKG Dashboard"
    st.set_page_config(page_title=title, page_icon="✈️", layout="wide")
    st.title(page_title + " at SKG/LGTS Airport" if page_title else "✈️ SKG/LGTS Airport Landings Dashboard")