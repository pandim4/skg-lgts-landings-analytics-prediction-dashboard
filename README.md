# ✈️ SKG Airport Aviation Data Analytics & Dashboard (2024)

This repository contains the code for my academic thesis project. It is a comprehensive data engineering and machine learning pipeline that collects, processes, and visualizes flight landing data and meteorological conditions (METAR) for **Thessaloniki Airport "Makedonia" (SKG / LGTS)** during the year 2024.

## 🗂️ Project Structure

The architecture of the project is divided into two independent microservices:

1. **Data Preparation (`data_preparation/`):** Contains Python scripts for data mining via the OpenSky Network, advanced preprocessing (Hampel filters, spatial DBSCAN for trajectory noise removal), and feature engineering (calculating aircraft crosswinds, categorizing weather conditions, handling METAR parsing).
2. **Dashboard (`dashboard/`):** A Streamlit application, fully containerized with Docker. It features interactive Plotly visualizations, a live geospatial flight path radar, and a pre-configured Machine Learning pipeline (Random Forest) for predicting runway usage configurations.

## 📊 About the Data (2024)

The project relies on real-world aviation and meteorological data from 2024:
* **Flight Trajectories:** Landing sequences at SKG mined from the OpenSky Network.
* **Meteorological Data:** Structured METAR reports for the airport.
* **Aviation Metadata:** Global aircraft specifications (manufacturers, engine types), airline identifiers, and Wake Turbulence Categories (WTC).

---

## 🚀 How to Run the Project

### Prerequisites
* Python 3.9+
* Docker & Docker Compose installed on your machine
* A SQL Database (e.g., PostgreSQL or SQLite)

### 1. Database Configuration
Create a `.env` file in the root directory and in the `dashboard` directory with your database connection string. For example:
```text
DB_URL=postgresql://user:password@localhost:5432/airport_db