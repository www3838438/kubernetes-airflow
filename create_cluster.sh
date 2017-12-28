#!/bin/bash

export AIRFLOW_HOME=${AIRFLOW_HOME:-"$(pwd)/airflow/opt/local/airflow/dags"}
export MYSQL_DATABASE=${MYSQL_DATABASE:-"airflow"}
export MYSQL_PASSWORD=${MYSQL_PASSWORD:-"airflow"}
export MYSQL_ROOT_PASSWORD=${MYSQL_ROOT_PASSWORD:-"airflow"}
export MYSQL_USER=${MYSQL_USER:-"airflow"}
export REDIS_PASSWORD=${REDIS_PASSWORD:-"airflow"}
export REDIS_PREFIX=${REDIS_PREFIX:-"airflow"}

envsubst < airflow.yml | kubectl create -f -
