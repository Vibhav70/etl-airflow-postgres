from airflow import DAG
from airflow.providers.http.operators.http import SimpleHttpOperator

from airflow.decorators import task
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.utils.dates import days_ago
import json
 
#Defining the DAG

with DAG(
    dag_id='nasa_apod_postgres',
    start_date=days_ago(1),
    schedule_interval='@daily',
    catchup=False
) as dag:
    # step1 : Creating the table if ot does not already exist

    @task
    def create_table():
        #initialize the postgres hook
        postgres_hook= PostgresHook(postgres_conn_id='my_postgres_connection')

        # SQL query to create the table
        create_table_query="""
        CREATE TABLE IF NOT EXISTS apod_data (
            id SERIAL PRIMARY KEY,
            title VARCHAR(255),
            explanation TEXT,
            url TEXT,
            date DATE,
            media_type VARCHAR(50)
        );

        """
        #execute the above query
        postgres_hook.run(create_table_query)


    #step2: Extracting the NASA API data(APOD) - Astronomy picture of the day[Extract Pipeline]

    extract_apod=SimpleHttpOperator(
        task_id='extract_apod',
        http_conn_id='nasa_api',    #Connection ID Defined in airflow for nasa api
        endpoint='planetary/apod',  # nasa api endpoint for APOD
        method='GET',
        data={"api_key":"{{conn.nasa_api.extra_dejson.api_key}}"},   #use the api key from the connection
        response_filter=lambda response:response.json(),
    )

    #Step3 : Transforming the data(Picking the data that needs to be savved in the databse)
    @task
    def transform_apod_data(response):
        apod_data={
            'title': response.get('title',''),  #if key not available then we get blank that's why empty quotes
            'explanation': response.get('explanation',''),
            'date':response.get('date',''),
            'media_type':response.get('media_type','')
        }
        return apod_data

    #Step4: Load the data into Postgres SQL
    @task
    def load_data_to_postgres(apod_data):
        #inittialize the postgreshook   
        postgres_hook=PostgresHook(postgres_conn_id='my_postgres_connection')

        #Define the SQL Insert Query
        insert_query = """
        INSERT INTO apod_data (title, explanation, url, date, media_type)
        VALUES (%s, %s, %s, %s, %s);
        """
        #execute SQL Query
        postgres_hook.run(insert_query,parameters=(
            apod_data['title'],
            apod_data['explanation'],
            apod_data['url'],
            apod_data['date'],
            apod_data['media_type']
        ))

    #step5: verify data using DBviwever


    #step6: define the task dependencies

    #Extract
    create_table() >> extract_apod ##Ensure the table is created before extraction
    api_response=extract_apod.output
    #Transform
    transformed_data=transform_apod_data(api_response)
    #load
    load_data_to_postgres(transformed_data)