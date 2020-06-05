Airflow
====

## Quick Start:
1. airflow needs a home, /airflow is the default,but you can lay foundation somewhere else if you prefer(optional)
export AIRFLOW_HOME=~/airflow

2. install from pypi using pip:
pip install apache-airflow

3. initialize the database
airflow initdb

4. Create a folder named 'dags' under /airflow.

5. Paste covid_india.py under this folder.

6. start the web server, default port is 8080: airflow webserver

7. start the scheduler: airflow scheduler

8. visit localhost:8080 in the browser and enable the covid dag in the home page.
