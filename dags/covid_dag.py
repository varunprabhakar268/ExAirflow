from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.operators.bash_operator import BashOperator
from airflow.operators.dummy_operator import DummyOperator
from airflow.utils.dates import days_ago

# other packages
from datetime import datetime
from datetime import timedelta
import pandas as pd
import requests
from pandas.io import gbq
from google.cloud import bigquery
import pydata_google_auth
import csv


default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': days_ago(0),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(seconds=5),
}

def get_cred():
    Credentials = pydata_google_auth.get_user_credentials(['https://www.googleapis.com/auth/bigquery'], )
    ProjectId = 'bigquerytest-271705'
    return Credentials,ProjectId

def source_to_csv():
    r = requests.get("https://api.covid19india.org/states_daily.json")
    response = r.json()

    my_dict = response['states_daily'][-3]
    date = my_dict['date']
    status = my_dict['status']
    del my_dict['status']
    del my_dict['date']
    del my_dict['tt']

    df = pd.DataFrame.from_dict(my_dict.items())
    df.columns = ['statecode', 'NewConfirmed']
    yest_date = datetime.now() - timedelta(days=1)
    df.insert(0, "Date", date, True)

    r2 = requests.get("https://api.covid19india.org/data.json")
    response2 = r2.json()

    dict2 = response2['statewise']
    df2 = pd.DataFrame.from_dict(dict2)
    df2 = df2[['state', 'statecode']]
    df2['statecode'] = df2['statecode'].str.lower()

    data = pd.merge(df, df2, on='statecode')
    data = data[['Date', 'state', 'NewConfirmed']]
    data.to_csv("/home/nineleaps/Data/CovidData_" + yest_date.strftime("%d-%b-%y") + ".csv", index=False)

def csv_to_table():
    yest_date = datetime.now() - timedelta(days=1)
    data = pd.read_csv('/home/nineleaps/Data/CovidData_' + yest_date.strftime("%d-%b-%y") + '.csv')
    Credentials,ProjectId = get_cred()
    data.to_gbq(destination_table='Covid19.statewise_daily_cases', project_id=ProjectId, if_exists='append')

def upload_percentage():
    yest_date = datetime.now() - timedelta(days=1)
    Credentials,ProjectId = get_cred()
    sql = 'select count(*) as TotalRows from Covid19.statewise_daily_cases'
    client = bigquery.Client(project=ProjectId, credentials=Credentials)
    df = client.query(sql).to_dataframe()

    input_file = open('/home/nineleaps/Data/CovidData_' + yest_date.strftime("%d-%b-%y") + '.csv', "r+")
    reader_file = csv.reader(input_file)
    value = len(list(reader_file))

    my_dict = {}
    my_dict['Date'] = yest_date.strftime("%d-%b-%y")
    my_dict['UploadPercentage'] = ((value - 1) * 100 /df['TotalRows'][0])

    df2 = pd.DataFrame()
    df2 = df2.append(my_dict, ignore_index=True)
    df2.to_gbq(destination_table='Covid19.upload_status', project_id=ProjectId, if_exists='append')

dag = DAG(
  dag_id='covid_dag',
  description='Test DAG',
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
  task_id='upload_percentage',
  python_callable=upload_percentage,
  dag=dag
)
# setting dependencies
task1 >> task2
task2 >> task3
# task2 >> run_this_last
# source_to_csv.set_downstream(csv_to_table)
