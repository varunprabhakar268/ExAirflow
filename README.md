#Covid India Pipepline

## Getting Started:

This is a Data On-Boarding Pipeline built from scratch using Apache Airflow in Python to fetch daily COVID19 cases from all states in India and ingest it to Big Query Table.
To know more about this pipeline. click on the link below.
https://docs.google.com/document/d/12JFKxV5eifEQpIHFPz1FlazLOB9CwPqJ9nRze_lPon0/edit

## Prerequisites

### SETUP AIRFLOW
​
1.  install from pypi using pip
 
    `pip install apache-airflow`
    
2. initialize the database
​
    `airflow initdb`
    ~~~~
### Install BigQuery
​
1. Install BigQuery using the following command:
    
   `pip install google-cloud-bigquery` 
   
   `pip install pandas-gbq -U`
      
2. Register the project on BigQuery and create a new Service Account.
​
3. Download the Json file that contains your key.
​
4.  export GOOGLE_APPLICATION_CREDENTIALS to point to the downloaded json file using the command:
    `export GOOGLE_APPLICATION_CREDENTIALS="key.json"` 
    
### Steps to be followed before running the application:
​
1. Copy and paste the Covid_India_SampleDag.py file into the dags folder inside your airflow.
​
    `home/ninleaps/airflow/dags`
​
2. Create a folder named Data in which the csv files will be stored.

3. To start the webserver, type:
    
    `airflow webserver -p 8080`
​
4. Start the scheduler:
    
    `airflow scheduler`
 
5. Open the browser and navigate to localhost:8080 to monitor the DAG.