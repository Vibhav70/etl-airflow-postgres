# ETL Pipeline with Apache Airflow

## Overview
This project demonstrates an ETL (Extract, Transform, Load) pipeline implemented using **Apache Airflow**. The pipeline fetches data from NASA's API, processes and transforms the data, and loads it into a **PostgreSQL database** using Airflow's **PostgresHook**.

---

## Features
- **Data Extraction:** Fetch data from NASA API.
- **Data Transformation:** Process and clean the extracted data.
- **Data Loading:** Store the transformed data into a PostgreSQL database.
- **Automation:** Schedule and manage workflows using Apache Airflow.

---

## Technologies Used
- **Apache Airflow** - Workflow orchestration.
- **PostgreSQL** - Database for storing processed data.
- **NASA API** - Source for data extraction.
- **Python** - Scripting and data transformation.

---

## Project Structure
```
project-directory/
├── dags/
│   ├── nasa_etl_pipeline.py
├── plugins/
│   ├── custom_operator.py
├── sql/
│   ├── create_table.sql
├── requirements.txt
├── README.md
```

---

## Requirements
- **Python 3.8+**
- **PostgreSQL Database**
- **Apache Airflow** (version 2.x)

---

## Setup Instructions

### 1. Clone the Repository
```
git clone <repository-url>
cd project-directory
```

### 2. Install Dependencies
```
pip install -r requirements.txt
```

### 3. Set Up PostgreSQL Database
1. Create a PostgreSQL database:
```
CREATE DATABASE nasa_data;
```
2. Run the SQL script to create the required table:
```
psql -d nasa_data -f sql/create_table.sql
```

### 4. Configure Airflow
1. Initialize Airflow:
```
airflow db init
```
2. Create an Airflow user:
```
airflow users create --username admin --firstname Admin --lastname User --role Admin --email admin@example.com
```
3. Start the Airflow webserver and scheduler:
```
airflow webserver --port 8080
airflow scheduler
```

### 5. Add Connection in Airflow
- Go to **Admin > Connections** in the Airflow UI.
- Add a new connection with the following details:
  - **Conn Id:** postgres_default
  - **Conn Type:** Postgres
  - **Host:** localhost
  - **Schema:** nasa_data
  - **Login:** postgres
  - **Password:** password
  - **Port:** 5432

### 6. Trigger the DAG
1. Place the DAG file (`nasa_etl_pipeline.py`) in the `dags/` folder.
2. Enable the DAG in the Airflow UI and trigger it.

---

## Pipeline Steps
1. **Extract Data:** Fetch data from NASA API endpoint.
2. **Transform Data:** Parse JSON response, clean data, and structure it.
3. **Load Data:** Insert data into PostgreSQL database using Airflow's PostgresHook.

---

## Sample SQL Schema
```sql
CREATE TABLE nasa_asteroids (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255),
    magnitude FLOAT,
    is_hazardous BOOLEAN,
    date DATE
);
```

---

## DAG Code Example
```python
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
import requests
import json
from datetime import datetime

# Define default args
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2023, 1, 1),
    'retries': 1
}

# Define DAG
dag = DAG(
    'nasa_etl_pipeline',
    default_args=default_args,
    description='ETL pipeline for NASA data',
    schedule_interval='@daily',
)

# ETL functions
def extract():
    url = 'https://api.nasa.gov/neo/rest/v1/feed?start_date=2023-01-01&api_key=DEMO_KEY'
    response = requests.get(url)
    data = response.json()
    with open('/tmp/nasa_data.json', 'w') as f:
        json.dump(data, f)

def transform():
    with open('/tmp/nasa_data.json') as f:
        data = json.load(f)
    transformed_data = []
    for asteroid in data['near_earth_objects']['2023-01-01']:
        transformed_data.append((
            asteroid['id'],
            asteroid['name'],
            asteroid['absolute_magnitude_h'],
            asteroid['is_potentially_hazardous_asteroid'],
            '2023-01-01'
        ))
    with open('/tmp/transformed_data.json', 'w') as f:
        json.dump(transformed_data, f)

def load():
    hook = PostgresHook(postgres_conn_id='postgres_default')
    with open('/tmp/transformed_data.json') as f:
        data = json.load(f)
    for record in data:
        hook.run("""
            INSERT INTO nasa_asteroids (id, name, magnitude, is_hazardous, date)
            VALUES (%s, %s, %s, %s, %s)
        """, parameters=record)

# Define tasks
extract_task = PythonOperator(
    task_id='extract_task',
    python_callable=extract,
    dag=dag,
)

transform_task = PythonOperator(
    task_id='transform_task',
    python_callable=transform,
    dag=dag,
)

load_task = PythonOperator(
    task_id='load_task',
    python_callable=load,
    dag=dag,
)

# Task pipeline
extract_task >> transform_task >> load_task
```

---

## Future Improvements
- Enhance error handling and logging.
- Optimize transformations for scalability.
- Integrate with cloud storage solutions (e.g., AWS S3 or GCS).
- Implement data validation and testing.

---

## Author
**Vibhav Sharma**

