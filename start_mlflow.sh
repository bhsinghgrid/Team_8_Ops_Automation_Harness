#!/bin/bash
source ./.venv/bin/activate
export MLFLOW_AUTH_CONFIG_PATH=$(pwd)/MagellanFrontend/mlflow_users.ini
export MLFLOW_FLASK_SERVER_SECRET_KEY='super-secret-key-for-csrf'
./.venv/bin/python -m mlflow server --host 127.0.0.1 --port 5001 --app-name basic-auth
deactivate
