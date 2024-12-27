# ETL Pipeline with Apache Airflow for NASA APOD

## Overview
This project demonstrates an ETL (Extract, Transform, Load) pipeline implemented using **Apache Airflow**. The pipeline fetches data from NASA's Astronomy Picture of the Day (APOD) API, processes and transforms the data, and loads it into a **PostgreSQL database** using Airflow's **PostgresHook**.

---

## Features
- **Data Extraction:** Fetch data from NASA APOD API.
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
│   ├── nasa_apod_postgres.py
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

### 5. Add Connections in Airflow
- **PostgreSQL Connection:**
  - Conn Id: `my_postgres_connection`
  - Conn Type: Postgres
  - Host: localhost
  - Schema: nasa_data
  - Login: postgres
  - Password: password
  - Port: 5432

- **NASA API Connection:**
  - Conn Id: `nasa_api`
  - Conn Type: HTTP
  - Host: `https://api.nasa.gov`
  - Extra: `{"api_key": "your_api_key_here"}`

### 6. Trigger the DAG
1. Place the DAG file (`nasa_apod_postgres.py`) in the `dags/` folder.
2. Enable the DAG in the Airflow UI and trigger it.

---

## Pipeline Steps
1. **Create Table:** Ensures the database table exists before processing data.
2. **Extract Data:** Fetch data from NASA APOD API endpoint.
3. **Transform Data:** Process and structure the data to match the database schema.
4. **Load Data:** Insert data into PostgreSQL database using Airflow's PostgresHook.

---

## Sample SQL Schema
```sql
CREATE TABLE apod_data (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255),
    explanation TEXT,
    url TEXT,
    date DATE,
    media_type VARCHAR(50)
);
```

---

## DAG Code Example
```python
from airflow import DAG
from airflow.providers.http.operators.http import SimpleHttpOperator
from airflow.decorators import task
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.utils.dates import days_ago
import json

with DAG(
    dag_id='nasa_apod_postgres',
    start_date=days_ago(1),
    schedule_interval='@daily',
    catchup=False
) as dag:

    @task
    def create_table():
        postgres_hook = PostgresHook(postgres_conn_id='my_postgres_connection')
        create_table_query = """
        CREATE TABLE IF NOT EXISTS apod_data (
            id SERIAL PRIMARY KEY,
            title VARCHAR(255),
            explanation TEXT,
            url TEXT,
            date DATE,
            media_type VARCHAR(50)
        );
        """
        postgres_hook.run(create_table_query)

    extract_apod = SimpleHttpOperator(
        task_id='extract_apod',
        http_conn_id='nasa_api',
        endpoint='planetary/apod',
        method='GET',
        data={"api_key": "{{conn.nasa_api.extra_dejson.api_key}}"},
        response_filter=lambda response: response.json(),
    )

    @task
    def transform_apod_data(response):
        apod_data = {
            'title': response.get('title', ''),
            'explanation': response.get('explanation', ''),
            'date': response.get('date', ''),
            'media_type': response.get('media_type', '')
        }
        return apod_data

    @task
    def load_data_to_postgres(apod_data):
        postgres_hook = PostgresHook(postgres_conn_id='my_postgres_connection')
        insert_query = """
        INSERT INTO apod_data (title, explanation, url, date, media_type)
        VALUES (%s, %s, %s, %s, %s);
        """
        postgres_hook.run(insert_query, parameters=(
            apod_data['title'],
            apod_data['explanation'],
            apod_data['url'],
            apod_data['date'],
            apod_data['media_type']
        ))

    create_table() >> extract_apod
    api_response = extract_apod.output
    transformed_data = transform_apod_data(api_response)
    load_data_to_postgres(transformed_data)
```

---

## Future Improvements
- Add error handling and retries for API failures.
- Implement data validation checks before loading.
- Optimize queries for scalability.
- Integrate cloud storage for data backups.

---

## Author
**Vibhav Sharma**

