from datetime import datetime, timedelta, time
import requests
import json
import os
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.empty import EmptyOperator
from airflow.sensors.time_delta import TimeDeltaSensor

def fetch_coin_data():
    # CoinGecko API URL
    url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,litecoin&vs_currencies=usd"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()

        # Specify the path to save the JSON file
        output_dir = r"C:\Users\sharif.neto\Documents\Dados\whiteboard_aak\data"  # Change to the desired directory
        os.makedirs(output_dir, exist_ok=True)  # Create the directory if it does not exist

        # Path to the original JSON
        original_json_path = os.path.join(output_dir, "original.json")

        # Create the original.json file if it does not exist
        if not os.path.exists(original_json_path):
            original_data = {
                "bitcoin": {"usd": 67107},
                "ethereum": {"usd": 2486.5},
                "litecoin": {"usd": 68.5},
            }
            with open(original_json_path, "w") as f:
                json.dump(original_data, f)

        # Load data from the original JSON
        with open(original_json_path, "r") as f:
            original_data = json.load(f)

        # Compare data and create a JSON with the differences
        differences = {}
        for coin, price_info in data.items():
            if coin in original_data:
                original_price = original_data[coin]["usd"]
                new_price = price_info["usd"]
                if original_price != new_price:
                    differences[coin] = {"original": original_price, "new": new_price}
            else:
                differences[coin] = {"original": None, "new": price_info["usd"]}

        # Save the differences in a JSON file if there are any
        differences_path = os.path.join(output_dir, "differences.json")
        with open(differences_path, "w") as f:
            json.dump(differences, f)

        return differences
    else:
        return {"error": f"Request failed: {response.status_code}"}

# Defining DAG parameters
default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime(2024, 10, 26),  # Set the start date here
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

# Creating the DAG
with DAG(
    "coinmarket_extraction",
    default_args=default_args,
    description="A DAG to extract cryptocurrency data from CoinGecko at 14:00 UTC -03:00",
    schedule_interval="@daily",
) as dag:

    # Start operator
    start = EmptyOperator(task_id="start")

    # TimeDeltaSensor to wait 15 minutes
    wait = TimeDeltaSensor(
        delta=timedelta(minutes=15),
        task_id="wait",
        poke_interval=60  # Check every 60 seconds
    )

    # Task to fetch data from CoinGecko
    fetch_data = PythonOperator(
        task_id="fetch_coin_data",
        python_callable=fetch_coin_data,
    )

    # End operator
    end = EmptyOperator(task_id="end")

    # Defining task order
    start >> wait >> fetch_data >> end
