# Configuration file for color schemes used in the application

model_colors = {
    # --- AIRBUS (Blue Shades) ---
    "A319": "#003366", # Navy Blue
    "A320": "#1f77b4", # Standard Blue
    "A321": "#4da6ff", # Sky Blue
    "A20N": "#005b96", # Ocean Blue (Neo)
    "A21N": "#b3d9ff", # Light Blue (Neo)
    "A345": "#00008b", # Dark Blue (A340)

    # --- BOEING (Orange Shades) ---
    "B738": "#ff7f0e", # Orange
    "B38M": "#e6550d", # Dark Orange (MAX)
    "B734": "#fdae6b", # Light Orange
    "B752": "#ffcc00", # Gold (757)
    
    # --- ATR (Green Shades) ---
    "AT72": "#2ca02c", # Forest Green
    "AT75": "#44ad44", # Medium Green
    "AT76": "#98df8a", # Light Green (Lawn)
    "AT43": "#006400", # Dark Green (ATR 42-300)
    "AT45": "#228b22", # Forest Green (ATR 42-500)
    
    # --- OTHER (Grey for the rest) ---
    "Other": "#888888"
}

airline_colors = {
    "Aegean Airlines": "#022267", # Dark Blue
    "Olympic Airlines": "#000e4b", # Dark Red
    "Sky Express": "#d60073", # Dark Green
    "Ryanair": "#eac62e",  # Dark Orange
    "Turkish Airlines": "#c10a0c", # Dark Purple
    "EuroWings": "#8b174d", # Dark Cyan
    "Wizz Air": "#441894", # Dark Orange
    "Transavia": "#00a65e", # Dark Purple
    "Austrian Airlines": "#E71C23", # Light Green
    "easyJet": "#f76300", # Light Orange
    "Other": "#888888" # Grey for the rest
}

countries_colors = {
    "Greece": "#055eb0", # Dark Blue
    "Ireland": "#00a64d", # Dark Red
    "Germany": "#000000", # Dark Green
    "Turkey": "#e30a17",  # Dark Orange
    "United Kingdom": "#010063", # Dark Purple
    "Hungary": "#477050", # Dark Cyan
    "Switzerland": "#f70000", # Dark Orange
    "Austria": "#c20f2d", # Dark Purple
    "Netherlands": "#204487", # Light Green
    "Belgium": "#f5d324", # Light Orange
    "Other": "#888888" # Grey for the rest
}

manufacturer_colors = {
    "AIRBUS": "#003366", # Navy Blue
    "BOEING": "#ff7f0e", # Orange
    "ATR": "#2ca02c", # Forest Green
    "Other": "#888888" # Grey for the rest
}

runway_colors = {
    "16": "#1976D2", # Dark Blue
    "34": "#E53935", # Dark Red
    "10": "#43A047", # Dark Green
    "28": "#FFA000"  # Dark Orange
}

visibility_colors = {
    "Medium": "#f5d324", # Light Orange
    "Low": "#c20f2d", # Dark Red
    "Critical": "#800080", # Dark Purple
    "High": "#43A047", # Light Green
}

wind_colors = {
    "Vardaris": "#e30a17", # Dark Red
    "Sea Breeze": "#1976D2", # Blue
    "Other": "#43A047" # Green
}

# Configuration for the orders of categories in visualizations
runway_order = {"runway_config": ["10", "16", "28", "34"]}
wind_direction_order = {"wind_direction_category": ["North", "Northeast", "East", "Southeast", "South", "Southwest", "West", "Northwest", "Variable"]}
day_period_order = ["Early Morning", "Morning", "Afternoon", "Evening", "Night"]
category_order = {
    "wtc": ["Light", "Medium", "Heavy"],  # Column order
    "engine": ["1", "2", "3", "4"]        # Row order
}

weather_order = {"weather_category": ["Drizzle", "Rain", "Thunderstorm","Mist","Fog"]}

visibility_order = {"visibility_category": ["Medium", "Low", "Critical"]}

all_categories_order = {
    "wind_direction_category": wind_direction_order["wind_direction_category"],
    "runway_config": runway_order["runway_config"],
    "weather_category": weather_order["weather_category"],
    "visibility_category": visibility_order["visibility_category"]
}

combined_order = {
    "wind_direction_category": wind_direction_order["wind_direction_category"],
    "runway_config": runway_order["runway_config"]
}