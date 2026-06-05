# NYC Taxi Operational & Financial Analysis (2023)

## Objective & Problem Statement
Analyzing a stratified sample of nearly 2 million rows of New York City Yellow Taxi transit data from the calendar year 2023 to uncover operational bottlenecks, evaluate pricing efficiencies, and transform raw transactional data into useful information for optimizing fleet operations.

## Data Source & Schema Reference
* **Dataset Source:** Official NYC Taxi & Limousine Commission (TLC) Trip Record Directory: https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page
* **Data Schema:** Official TLC Yellow Taxi Data Dictionary: https://www.nyc.gov/assets/tlc/downloads/pdf/data_dictionary_trip_records_yellow.pdf

## Key Tech Stack
* Python
* Pandas
* GeoPandas
* Seaborn
* Matplotlib

## Key Discoveries
* **The Pricing Paradox:** Average fare per mile spikes sharply during weekday morning peak hours (8 AM - 9 AM). This occurs because taxi meters switch to time-based idling calculations in gridlock, meaning passengers actively pay for time spent stuck in traffic while covering very little physical distance.
* **Traffic Bottlenecks:** Identified clear structural bottlenecks between 8 AM - 10 AM and 4 PM - 6 PM on weekdays, where average fleet speeds drop to single digits (~7-9 MPH). This stands in stark contrast to late-night windows (2 AM - 5 AM), where speeds maximize well above 15 MPH.
* **Data Anomaly Verification:** Proved that while dropping zero-distance trips globally is analytically incorrect (as they generate valid base flag-drop revenue when passengers board and cancel within a zone), it is mathematically vital to filter them out locally to prevent division-by-zero errors during rate indexing.

## Repository Contents
* `NYC_Taxi_EDA/EDA_NYC_Taxi_Analysis_Praveen_Natarajan.ipynb` - Local notebook configured to read dataset files from local storage.
* `NYC_Taxi_EDA/EDA_Assg_NYC_Taxi_cloud.ipynb` - Cloud notebook configured to stream the dataset via Google Drive storage.
* `NYC_Taxi_EDA/EDA_NYC_Taxi_Analysis_Praveen_Natarajan.pdf` - Final compiled executive summary report.
* `NYC_Taxi_EDA/*.png` - Generated analytical visualization trends (including maps, revenue spreads, monthly distribution, and hourly velocity plots).
