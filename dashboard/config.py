

# Configuration file for color schemes used in the application

model_colors = {
    # --- AIRBUS (Αποχρώσεις του Μπλε) ---
    "A319": "#003366", # Navy Blue
    "A320": "#1f77b4", # Standard Blue
    "A321": "#4da6ff", # Sky Blue
    "A20N": "#005b96", # Ocean Blue (Neo)
    "A21N": "#b3d9ff", # Light Blue (Neo)
    "A345": "#00008b", # Dark Blue (A340)

    # --- BOEING (Αποχρώσεις του Πορτοκαλί) ---
    "B738": "#ff7f0e", # Orange
    "B38M": "#e6550d",# Dark Orange (MAX)
    "B734": "#fdae6b", # Light Orange
    "B752": "#ffcc00", # Gold (757)
    
    # --- ATR (Αποχρώσεις του Πράσινου) ---
    "AT72": "#2ca02c", # Forest Green
    "AT75": "#44ad44", # Medium Green
    "AT76": "#98df8a", # Light Green (Lawn)
    "AT43": "#006400", # Dark Green (ATR 42-300)
    "AT45": "#228b22", # Forest Green (ATR 42-500)
    
    # --- ΛΟΙΠΑ (Γκρι για ό,τι περισσέψει) ---
    "Other": "#888888"
}

airline_colors = {
    "Aegean Airlines": "#022267", # Μπλε-Σκούρο
    "Olympic Airlines": "#000e4b", # Κόκκινο-Σκούρο
    "Sky Express": "#d60073", # Πράσινο-Σκούρο
    "Ryanair": "#eac62e",  # Πορτοκαλί-Σκούρο
    "Turkish Airlines": "#c10a0c", # Μωβ-Σκούρο
    "EuroWings": "#8b174d", # Κυανό-Σκούρο
    "Wizz Air": "#441894", # Πορτοκαλί-Σκούρο
    "Transavia": "#00a65e", # Μωβ-Σκούρο
    "Austrian Airlines": "#E71C23", # Πράσινο-Φωτό
    "easyJet": "#f76300", # Πορτοκαλί-Φωτό
    "Other": "#888888" # Γκρι για ό,τι περισσέψει
}

countries_colors = {
    "Greece": "#055eb0", # Μπλε-Σκούρο
    "Ireland": "#00a64d", # Κόκκινο-Σκούρο
    "Germany": "#000000", # Πράσινο-Σκούρο
    "Turkey": "#e30a17",  # Πορτοκαλί-Σκούρο
    "United Kingdom": "#010063", # Μωβ-Σκούρο
    "Hungary": "#477050", # Κυανό-Σκούρο
    "Switzerland": "#f70000", # Πορτοκαλί-Σκούρο
    "Austria": "#c20f2d", # Μωβ-Σκούρο
    "Netherlands": "#204487", # Πράσινο-Φωτό
    "Belgium": "#f5d324", # Πορτοκαλί-Φωτό
    "Other": "#888888" # Γκρι για ό,τι περισσέψει
}

manufacturer_colors = {
    "AIRBUS": "#003366", # Navy Blue
    "BOEING": "#ff7f0e", # Orange
    "ATR": "#2ca02c", # Forest Green
    "Other": "#888888" # Γκρι για ό,τι περισσέψει
}


runway_colors = {
    "16": "#1976D2", # Μπλε-Σκούρο
    "34": "#E53935", # Κόκκινο-Σκούρο
    "10": "#43A047", # Πράσινο-Σκούρο
    "28": "#FFA000"  # Πορτοκαλί-Σκούρο
}

visibility_colors = {
    "Medium": "#f5d324", # Πορτοκαλί-Φωτό
    "Low": "#c20f2d", # Κόκκινο-Σκούρο
    "Critical": "#800080", # Μωβ-Σκούρο
    "High": "#43A047", # Πράσινο-Φωτό
}

wind_colors = {
    "Vardaris": "#e30a17", # Κόκκινο-Σκούρο
    "Sea Breeze": "#1976D2", # Blue
    "Other": "#43A047" # Green
}



# Configuration for the orders of categories in visualizations
runway_order = {"runway_config": ["10", "16", "28", "34"]}
wind_direction_order = {"wind_direction_category": ["North", "Northeast", "East", "Southeast", "South", "Southwest", "West", "Northwest", "Variable"]}
day_period_order = ["Early Morning", "Morning", "Afternoon", "Evening", "Night"]
category_order = {
    "wtc": ["Light", "Medium", "Heavy"],  # Σειρά για τις στήλες
    "engine": ["1", "2", "3", "4"]        # Σειρά για τις γραμμές (αν είναι strings)
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
