from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.operators.bash_operator import BashOperator
from airflow.operators.dummy_operator import DummyOperator
from airflow.utils.dates import days_ago
from airflow.hooks.base_hook import BaseHook
import logging

from datetime import datetime
from datetime import timedelta
import pandas as pd
import requests
from pandas.io import gbq
from google.cloud import bigquery
from google.oauth2 import service_account
import pydata_google_auth
import csv

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': days_ago(0),
    'email': ['captaincold268@gmail.com'],
    'email_on_failure': True,
    'email_on_retry': True,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}
previous_day = datetime.now() - timedelta(days=1)
credentials = service_account.Credentials.from_service_account_file('/home/nineleaps/BQKey.json',)
project_id = credentials.project_id

def get_confirmed_cases():
    try:
        r = requests.get("https://api.covid19india.org/states_daily.json")
        r.raise_for_status()
        response = r.json()
        confirmed_cases = response['states_daily'][-3]
        del confirmed_cases['status']
        del confirmed_cases['date']
        del confirmed_cases['tt']
        confirmed_cases_df = pd.DataFrame.from_dict(confirmed_cases.items())
        confirmed_cases_df.columns = ['statecode', 'confirmed_cases']
        confirmed_cases_df.insert(0, "date", previous_day.strftime("%d-%b-%y"), True)
        return confirmed_cases_df
    except requests.exceptions.HTTPError as err:
        logging.error('Http Error: ' + str(err))
        raise SystemExit(err)


def get_states_list():
    try:
        r = requests.get("https://api.covid19india.org/data.json")
        r.raise_for_status()
        response = r.json()
        state_list = response['statewise']
        state_list_df = pd.DataFrame.from_dict(state_list)
        state_list_df = state_list_df[['state', 'statecode']]
        state_list_df['statecode'] = state_list_df['statecode'].str.lower()
        return state_list_df
    except requests.exceptions.HTTPError as err:
        logging.error('Http Error: ' + str(err))
        raise SystemExit(err)


def get_covid_data():
    confirmed_case_df = get_confirmed_cases()
    state_list_df = get_states_list()
    covid_data = pd.merge(confirmed_case_df, state_list_df, on='statecode')
    covid_data = covid_data[['date', 'state', 'confirmed_cases']]
    return covid_data


def source_to_csv():
    data = get_covid_data()
    data.to_csv("/home/nineleaps/airflow/Data/CovidData_" + previous_day.strftime("%d-%b-%y") + ".csv", index=False)
    logging.info("successfully created csv.")


def csv_to_table():
    try:
        data = pd.read_csv('/home/nineleaps/airflow/Data/CovidData_' + previous_day.strftime("%d-%b-%y") + '.csv')
        data.to_gbq(destination_table='Covid19.statewise_daily_cases', project_id=project_id,credentials=credentials, if_exists='replace')
        logging.info("successfully uploaded data to table.")
    except GenericGBQException as e:
        logging.error(str(e))
        raise SystemExit(err)


def get_row_count_from_table():
    try:
        sql = 'select count(*) as total_rows from Covid19.statewise_daily_cases'
        total_rows_df = gbq.read_gbq(query=sql, project_id=project_id,credentials=credentials)
        return total_rows_df['total_rows'][0]
    except GenericGBQException as e:
        logging.error(str(e))
        raise SystemExit(err)


def get_csv_row_count():
    input_file = open('/home/nineleaps/airflow/Data/CovidData_' + previous_day.strftime("%d-%b-%y") + '.csv', "r+")
    reader_file = csv.reader(input_file)
    return len(list(reader_file))


def get_upload_status(csv_row_count, table_row_count):
    upload_status = {}
    upload_status['date'] = previous_day.strftime("%d-%b-%y")
    upload_status['upload_percentage'] = ((csv_row_count - 1) * 100 / table_row_count)
    upload_status_df = pd.DataFrame()
    upload_status_df = upload_status_df.append(upload_status, ignore_index=True)
    return upload_status_df


def push_upload_status_to_table():
    try:
        table_row_count = get_row_count_from_table()
        csv_row_count = get_csv_row_count()
        upload_status_df = get_upload_status(csv_row_count, table_row_count)
        upload_status_df.to_gbq(destination_table='Covid19.upload_status', project_id=project_id,credentials=credentials, if_exists='replace')
        logging.info("successfully uploaded data to table.")
    except GenericGBQException as e:
        logging.error(str(e))
        raise SystemExit(err)


dag = DAG(
    dag_id='covid_india_dag',
    description='A DAG to fetch and upload statewise covid data to BQ',
    default_args=default_args,
    schedule_interval="@daily",
    catchup=False)

task1 = PythonOperator(
    task_id='source_to_csv',
    python_callable=source_to_csv,
    dag=dag)

task2 = PythonOperator(
    task_id='csv_to_table',
    python_callable=csv_to_table,
    dag=dag
)

task3 = PythonOperator(
    task_id='upload_status_to_table',
    python_callable=push_upload_status_to_table,
    dag=dag
)

task1 >> task2
task2 >> task3
