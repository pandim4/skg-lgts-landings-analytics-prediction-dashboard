# ✈️ SKG / LGTS Airport Landings Dashboard & ML Runway Prediction

![Python](https://img.shields.io/badge/Python-3.9-blue?style=for-the-badge\&logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge\&logo=streamlit\&logoColor=white)
![Plotly](https://img.shields.io/badge/Plotly-3F4F75?style=for-the-badge\&logo=plotly\&logoColor=white)
![Scikit-Learn](https://img.shields.io/badge/Scikit_Learn-F7931E?style=for-the-badge\&logo=scikit-learn\&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge\&logo=postgresql\&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge\&logo=docker\&logoColor=white)

An end-to-end Data Engineering, Analytics, and Machine Learning project analyzing flight landings and weather conditions at **Thessaloniki Airport "Makedonia" (SKG/LGTS)** using a comprehensive **2024 dataset**. The system dynamically processes telemetry and METAR data to predict the active runway configuration.

---

# ✨ Features & Visualizations

This project features an extensive **Exploratory Data Analysis (EDA)** module, providing deep insights into the 2024 operational data.

## 1. 🗺️ Interactive Flight Path Radar & 3D Profiling

Visualizes actual descent paths and landing trajectories using spatial clustering (**DBSCAN**) and Plotly 3D maps.

> ![Dashboard Overview](assets/dashboard_overview.png)

## 2. 🤖 ML Runway Prediction

Uses a **Random Forest Classifier** to predict the active runway (**10, 16, 28, or 34**) for **2, 12, and 24-hour horizons**.

### 📊 Model Performance

* **82% terminal weighted accuracy** on 2024 operational data.
* Time-aware validation using **TimeSeriesSplit**.
* Feature importance visualization included.

> ![Runway Prediction](assets/runway_prediction.png)

## 3. 🌦️ Advanced Weather & METAR Analysis (EDA)

Comprehensive meteorological analysis of 2024 operational conditions.

### Key Findings

* **Vardaris (NW) winds** trigger **Runway 34** usage **98.2%** of the time.
* **Sea breeze conditions** shift **93.9%** of landings to **Runway 16**.
* Wind behavior strongly correlates with runway configuration and landing distribution.

> ![Wind Rose](assets/wind_rose.png)
> ![Vardaris Conditions](assets/vardaris.png)

## 4. 🛩️ Temporal & Fleet Analytics (EDA)

In-depth temporal analysis and fleet composition insights for 2024 traffic.

### Traffic Insights

* **Peak traffic period:** July–September.
* Approximately **2,100 landings/month** during summer peaks.

### Fleet Composition

* **Airbus:** 55.9%
* **Boeing:** 28.9%
* Remaining traffic includes turboprops, regional jets, and business aviation.

> ![Fleet Analysis](assets/airline.png)

---

# 🧠 Architecture & Pipeline

## 1. Data Mining

Extracts large-scale historical ADS-B flight data for 2024 using the **OpenSky Network API**.

## 2. Data Cleaning & Preprocessing

* Missing-value handling
* Noise reduction using **Hampel filters**
* Spatial clustering with **DBSCAN**
* Rule-Based Landing Classifier for filtering non-landing operations

## 3. Feature Engineering

* Crosswind/headwind calculations
* Cyclical encoding for temporal continuity:

  * sine/cosine transformations
  * hour/day seasonality preservation

## 4. Machine Learning

* `RandomForestClassifier`
* `TimeSeriesSplit` cross-validation
* Runway prediction for multiple forecast horizons

## 5. Database Stack

Historical and processed data stored using:

* **PostgreSQL**
* **SQLAlchemy ORM**

---

# 🚀 Installation & Setup

## Prerequisites

* Python **3.9+**
* Docker & Docker Compose
* SQL Database environment (PostgreSQL recommended)

---

## 1. Clone the Repository

```bash
git clone https://github.com/pandim4/skg-lgts-landings-analytics-prediction-dashboard.git
cd skg-lgts-landings-analytics-prediction-dashboard
```

---

## 2. Configure Environment Variables

Create a `.env` file in the project root:

```env
DB_URL=postgresql://user:password@localhost:5432/airport_db
```

You may also need a `.env` file inside the `dashboard/` directory depending on your deployment setup.

---

## 3. Data Unzipping

Navigate to the `data_preparation/` directory and unzip the `data.zip` archive.

This archive contains the raw operational datasets used to reproduce the project's results.

---

# 🗄️ Database Initialization

You can either:

* Load precomputed tables (**recommended**)
* Run the full ETL pipeline from scratch

---

## Option A — Quick Setup (Recommended)

Navigate to the `data_preparation/` directory and execute:

```bash
python create_ready_tables.py
```

This script automatically loads all preprocessed final tables into your configured database.

---

## Option B — Full Data Preprocessing Pipeline

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Run the Mining Script

```bash
python landings_mining.py
```

### Workflow Steps

#### Select Data Source

The script allows you to:

* use existing data
* mine new data from OpenSky

Using existing data is recommended initially because full mining is computationally expensive.

#### Select Timeframe

Choose how many quarters of the year to process:

* `1` → Q1
* `2` → Q1 + Q2
* etc.

#### OpenSky Authentication

If mining new data:

* an **OpenSky Network** account is required
* credentials may be entered through the browser popup
* alternatively configure the `traffic` library authentication manually

### Final Processing

After mining completes:

```bash
python main.py
```

This runs the preprocessing pipeline and generates the final tables.

---

# 🤖 Machine Learning Execution

Navigate to the `machine_learning/` directory.

The ML scripts:

* train predictive models
* evaluate forecasting performance
* generate:

  * confusion matrices
  * feature importance chart
  * runway prediction metrics

---

# 📊 Launching the Dashboard

Ensure Docker is installed and running.

From the root directory execute:

```bash
docker-compose up --build
```

This will:

* containerize the application
* launch the Streamlit dashboard
* expose the dashboard through your browser

---

# 🧩 Technologies Used

* Python
* Streamlit
* Plotly
* Scikit-Learn
* PostgreSQL
* SQLAlchemy
* Docker
* OpenSky Network API

---

# 📌 Project Highlights

✅ End-to-end aviation analytics pipeline
✅ Real-world ADS-B & METAR integration
✅ Advanced EDA and meteorological analysis
✅ Time-aware machine learning forecasting
✅ Interactive Streamlit dashboard visualization
✅ Dockerized deployment workflow
