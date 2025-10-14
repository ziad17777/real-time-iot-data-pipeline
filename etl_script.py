import csv
import json
import sqlite3
from datetime import datetime
import pandas as pd
import os


DB_NAME = 'logs.db'
TABLE_NAME = 'daily_metrics'
LOG_FOLDER = 'sample_logs'

def create_database_and_table():
    """Initializes the SQLite database and creates the necessary table if they don't exist."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
            metric_date TEXT PRIMARY KEY,
            min_value REAL,
            max_value REAL,
            avg_value REAL
        )
    ''')
    conn.commit()
    conn.close()

def extract_from_csv(file_path):
    """Extracts data from a CSV file."""
    
    return pd.read_csv(file_path)

def extract_from_json(file_path):
    """Extracts data from a JSON file."""
    
    return pd.read_json(file_path)

def transform_data(df):
    """
    Transforms the raw log data into daily aggregated metrics using pandas.
    - Converts timestamps to datetime objects.
    - Groups data by day.
    - Calculates min, max, and average of 'value' for each day.
    """
    if df.empty:
        return None

    df['value'] = pd.to_numeric(df['value'], errors='coerce')
    df.dropna(subset=['value'], inplace=True)
    
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['metric_date'] = df['timestamp'].dt.date

    daily_aggregations = df.groupby('metric_date')['value'].agg(['min', 'max', 'mean']).reset_index()
    
    daily_aggregations.rename(columns={'min': 'min_value', 'max': 'max_value', 'mean': 'avg_value'}, inplace=True)
    
    return daily_aggregations

def load_to_db(transformed_data):
    """Loads the transformed DataFrame into the SQLite database."""
    if transformed_data is None or transformed_data.empty:
        print("No data to load.")
        return

    conn = sqlite3.connect(DB_NAME)
    transformed_data.to_sql(
        TABLE_NAME, 
        conn, 
        if_exists='replace', 
        index=False,       
        dtype={'metric_date': 'TEXT PRIMARY KEY'} # Ensures the primary key is set
    )
    conn.close()
    print(f"Successfully loaded {len(transformed_data)} rows into {TABLE_NAME}.")

def process_logs():
    """Main function to run the ETL process for all log files in the specified folder."""
    create_database_and_table()
    
    if not os.path.exists(LOG_FOLDER):
        print(f"Error: Log folder '{LOG_FOLDER}' not found. Please create this directory and add your log files.")
        return

    all_dfs = []

    for filename in os.listdir(LOG_FOLDER):
        file_path = os.path.join(LOG_FOLDER, filename)
        print(f"Extracting from {filename}...")
        try:
            if filename.endswith('.csv'):
                all_dfs.append(extract_from_csv(file_path))
            elif filename.endswith('.json'):
                all_dfs.append(extract_from_json(file_path))
        except Exception as e:
            print(f"Could not process file {filename}: {e}")

    if all_dfs:
        combined_df = pd.concat(all_dfs, ignore_index=True)
        
        print("Transforming data...")
        transformed = transform_data(combined_df)
        
        print("Loading data into database...")
        load_to_db(transformed)
    else:
        print(f"No valid log files found to process in '{LOG_FOLDER}'.")

if __name__ == '__main__':
    process_logs()

