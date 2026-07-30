CyberNova Analytics Dashboard

A role-based business intelligence dashboard built for CyberNova Ltd, a fictional cybersecurity company operating across the SADC region (Botswana, South Africa, Namibia, Zimbabwe, Angola, Zambia, Malawi, Mozambique, Lesotho, and Eswatini). The project simulates web server traffic, cleans and analyzes it, runs it through several machine learning models, and presents the results in an interactive Streamlit dashboard with authenticated, role-based access.

Built using the CRISP-DM methodology as part of a Business Intelligence & Data Analytics portfolio project.

Features
Synthetic web log generation — realistic traffic data across 10 SADC countries, weighted by actual internet penetration

Data cleaning & preprocessing — structured CRISP-DM style inspection and cleaning pipeline

Machine learning pipeline (ml_analysis.py):
Traffic forecasting
Anomaly detection (Isolation Forest)
Market clustering (K-Means)
Conversion prediction (Random Forest Classifier/Regressor)

Interactive Streamlit dashboard with:
Secure login (bcrypt password hashing)
Role-based access control — Viewer, Analyst, Administrator
Six dashboard views: Strategic Market Identification, Tactical Engagement Trends, Business Value & AI Predictions, Operational Reporting, System Governance & Audit, and a User Manual
Session timeout handling
PDF and Excel report export

Standalone chart generation (data_analysis.py) producing 12 branded matplotlib visualizations (KPI summaries, traffic by country, hourly/daily trends, heatmaps, and more), saved to the charts/ folder

Tech Stack
Purpose	Library
Data manipulation	pandas, numpy
Visualization	matplotlib, plotly
Dashboard framework	streamlit
Machine learning	scikit-learn
Authentication	bcrypt
Reporting/export	fpdf (fpdf2), xlsxwriter

Project Structure
PythonProject_CyberNova/
├── dashboard.py                        # Main Streamlit app (auth, roles, views)
├── data_analysis.py                    # Generates static branded charts
├── data_cleaning_and_preprocessing.py  # CRISP-DM data cleaning pipeline
├── ml_analysis.py                      # ML models: forecasting, clustering, anomaly & conversion prediction
├── web_server_log.py                   # Synthetic web log data generator
├── charts/                             # Output folder for generated PNG charts
├── CyberNova_Web_Logs.csv              # Simulated web server log dataset
├── requirements.txt                    # Python dependencies
└── README.md

Getting Started

1. Clone the repository
bash
git clone https://github.com/yourusername/CyberNova.git
cd CyberNova
2. Create a virtual environment
bash
python -m venv .venv

Activate it:

Windows: .venv\Scripts\activate
macOS/Linux: source .venv/bin/activate
3. Install dependencies
bash
pip install -r requirements.txt
4. Generate the dataset (if not already present)
bash
python web_server_log.py
5. Run the dashboard
bash
streamlit run dashboard.py

This opens the app in your browser at http://localhost:8501.

Optional: Standalone scripts

Generate static charts without the dashboard:

bash
python data_analysis.py

Run the ML pipeline on its own and print results:

bash
python ml_analysis.py

Run the data cleaning report:

bash
python data_cleaning_and_preprocessing.py
Roles & Access
Role	Access
Viewer	Strategic Market Identification, Tactical Engagement Trends, Business Value & AI Predictions, User Manual
Analyst	All Viewer pages + Operational Reporting
Administrator	Full access, including System Governance & Audit

Login credentials are managed internally via bcrypt-hashed passwords and are not included in this repository for security reasons.

Notes
All web traffic data is synthetically generated for demonstration purposes and does not represent real user activity.
This project was developed as part of an academic/portfolio Business Intelligence & Data Analytics body of work.

Author

Michelle Onneile Nkwe