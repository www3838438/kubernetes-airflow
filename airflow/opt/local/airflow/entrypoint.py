#!/usr/bin/env python
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from cryptography.fernet import Fernet
import os
import pystache
import subprocess
import sys
import time


print(os.environ)
FERNET_KEY = Fernet.generate_key().decode()

AIRFLOW_HOME = os.environ['AIRFLOW_HOME']
AIRFLOW_EXECUTOR = os.environ['AIRFLOW__CORE__EXECUTOR']

if 'AIRFLOW_INITIALIZE_DATABASE' in os.environ:
    AIRFLOW_INITIALIZE_DATABASE = True
else:
    AIRFLOW_INITIALIZE_DATABASE = False


def is_readable(path):
    return os.path.isfile(path)


def airflow_cli(command):
    # importing airflow must be after coping user specified config file
    import airflow.bin.cli
    parser = airflow.bin.cli.CLIFactory.get_parser()
    args = parser.parse_args(command)
    print(args)
    args.func(args)


def execute_command_with_returncode(command):
    # 0 is success
    try:
        returncode = subprocess.call(command.split(), shell=False)
    except subprocess.CalledProcessError as e:
        print("return code: {0}".format(e.returncode))
        print("command: {0}".format(e.cmd))
        print("output: {0}".format(e.output))
        raise
    return returncode


def copy_config_template():
    path_to_config_template = os.path.join(AIRFLOW_HOME, 'airflow.cfg.template')
    try:
        with open(path_to_config_template, 'r') as f:
            lines = f.readlines()
    except IOError as e:
        print(e)

    rendered_config = [pystache.render(l, dict(os.environ)) for l in lines]

    path_to_config = os.path.join(AIRFLOW_HOME, 'airflow.cfg')
    try:
        with open(path_to_config, 'w') as f:
            for line in rendered_config:
                f.write(line)
    except IOError as e:
        print(e)


def healthcheck(host, port):
    max_loop = 20
    for i in range(0, max_loop):
        command = 'nc -z {0} {1}'
        command = command.format(host, port)
        print(command)
        returncode = execute_command_with_returncode(command)
        # without error
        if returncode == 0:
            return 0
        print('  Wait 10 sec')
        time.sleep(10)
    print('Reached to the maximum number of loop')
    sys.exit(1)


def wait_postgres():
    host = os.environ['POSTGRES_HOST']
    port = os.environ['POSTGRES_PORT']
    healthcheck(host, port)
    return 0


def wait_mysql():
    host = os.environ['MYSQL_HOST']
    port = os.environ['MYSQL_PORT']
    healthcheck(host, port)
    return 0


def wait_redis():
    host = os.environ['REDIS_HOST']
    port = os.environ['REDIS_PORT']
    healthcheck(host, port)
    return 0


def wait_webserver():
    host = os.environ['AIRFLOW__WEBSERVER__WEB_SERVER_HOST']
    port = os.environ['AIRFLOW__WEBSERVER__WEB_SERVER_PORT']
    healthcheck(host, port)
    return 0


def main():
    airflow_subcommand = sys.argv[1]
    path_to_config = os.path.join(AIRFLOW_HOME, 'airflow.cfg')

    # if airflow.cfg exists, it's first time to run airflow
    print('copy template to {0}'.format(path_to_config))
    copy_config_template()

    # if initialize flag is true
    if AIRFLOW_INITIALIZE_DATABASE:
        print('Initializing database')
        wait_mysql()
        airflow_cli(['initdb'])

    if airflow_subcommand != 'webserver':
        wait_webserver()

    if AIRFLOW_EXECUTOR == 'CeleryExecutor':
        print('Waiting for DB...')
        wait_mysql()
        # wait for redis
        print('Wait for redis ...')
        if airflow_subcommand in ['webserver', 'worker', 'scheduler', 'flower']:
            wait_redis()

        airflow_cli([airflow_subcommand])

    elif AIRFLOW_EXECUTOR == 'LocalExecutor':
        airflow_cli([airflow_subcommand])
        if airflow_subcommand == 'version':
            return 0
    else:
        # By default we use SequentialExecutor
        airflow_cli([airflow_subcommand])
        if airflow_subcommand == 'version':
            return 0


if __name__ == '__main__':
    main()
