# ✈️ SKG / LGTS Airport Landings Dashboard & ML Runway Prediction

![Python](https://img.shields.io/badge/Python-3.9-blue?style=for-the-badge&logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![Plotly](https://img.shields.io/badge/Plotly-3F4F75?style=for-the-badge&logo=plotly&logoColor=white)
![Scikit-Learn](https://img.shields.io/badge/Scikit_Learn-F7931E?style=for-the-badge&logo=scikit-learn&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)

An end-to-end Data Engineering, Analytics, and Machine Learning project analyzing flight landings and weather conditions at **Thessaloniki Airport "Makedonia" (SKG/LGTS)** using a comprehensive **2024 dataset**. The system dynamically processes telemetry and METAR data to predict the active runway configuration.

---

## ✨ Features & Visualizations

[cite_start]This project features an extensive **Exploratory Data Analysis (EDA)** module, providing deep insights into the 2024 operational data[cite: 196].

### 1. 🗺️ Interactive Flight Path Radar & 3D Profiling
[cite_start]Visualizes actual descent paths and landing trajectories using spatial clustering (DBSCAN) and Plotly 3D maps[cite: 107, 188].
> ![Dashboard Overview](assets/dashboard_overview.jpg)

### 2. 🤖 ML Runway Prediction
[cite_start]Uses a Random Forest Classifier to predict the active runway (10, 16, 28, or 34) for 2, 12, and 24-hour horizons[cite: 167, 184]. [cite_start]The model achieved an **82% terminal weighted accuracy** based on 2024 data[cite: 7, 266].
> ![Runway Prediction](assets/runway_prediction.jpg)

### 3. 🌦️ Advanced Weather & METAR Analysis (EDA)
[cite_start]Comprehensive **EDA** of 2024 meteorological phenomena[cite: 195]. Key findings:
* [cite_start]**Vardaris (NW) winds** trigger Runway 34 usage 98.2% of the time[cite: 202].
* [cite_start]**Sea Breezes** shift 93.9% of landings to Runway 16[cite: 202].
> ![Wind Rose](assets/wind_rose.png)
> ![Vardaris Conditions](assets/vardaris.png)

### 4. 🛩️ Temporal & Fleet Analytics (EDA)
[cite_start]In-depth **EDA** and **temporal analysis** of 2024 traffic[cite: 196].
* [cite_start]**Traffic Peaks:** Summer months (July-September) with ~2,100 landings/month[cite: 197].
* [cite_start]**Fleet Insights:** Dominated by Airbus (55.9%) and Boeing (28.9%)[cite: 206].
> ![Fleet Analysis](assets/airline.png)
---

## 🧠 Architecture & Pipeline 

1. **Data Mining:** Extracts massive historical ADS-B flight data for the year 2024 via the OpenSky Network API.
2. **Data Cleaning & Preprocessing:** Handles missing values and noise using **Hampel filters** and **DBSCAN**. Includes a **Rule-Based Landing Classifier** to filter out non-landing operations.
3. **Feature Engineering:** Calculates crosswinds/headwinds and performs cyclical encoding for time variables (sine/cosine transformations) to preserve continuity.
4. **Machine Learning:** Utilizes a `RandomForestClassifier` with `TimeSeriesSplit` cross-validation to account for temporal data dependencies.
5. **Database Stack:** Historical 2024 data is stored and analyzed via **PostgreSQL** using the **SQLAlchemy ORM**.

---

## 🚀 Installation & Setup

To run the project locally, ensure you have Docker installed.

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/yourusername/skg-runway-prediction.git](https://github.com/yourusername/skg-runway-prediction.git)
   cd skg-runway-prediction

## 🚀 How to Run the Project

### Prerequisites
* Python 3.9+
* Docker & Docker Compose installed on your machine
* A SQL Database (e.g., PostgreSQL or SQLite)

### 1. Database Configuration
Create a `.env` file in the root directory and in the `dashboard` directory with your database connection string. For example:
```text
DB_URL=postgresql://user:password@localhost:5432/airport_db