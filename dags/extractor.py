from datetime import datetime, timedelta
import requests
import json
import os
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.empty import EmptyOperator


def fetch_coin_data():
    # URL da API CoinGecko
    url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,litecoin&vs_currencies=usd"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()

        # Especifica o caminho para salvar o arquivo JSON
        output_dir = r"C:\Users\sharif.neto\Documents\Dados\whiteboard_aak\data"  # Altere para o diretório desejado
        os.makedirs(output_dir, exist_ok=True)  # Cria o diretório se não existir

        # Caminho do JSON original
        original_json_path = os.path.join(output_dir, "original.json")

        # Criar o arquivo original.json se não existir
        if not os.path.exists(original_json_path):
            original_data = {
                "bitcoin": {"usd": 67107},
                "ethereum": {"usd": 2486.5},
                "litecoin": {"usd": 68.5},
            }
            with open(original_json_path, "w") as f:
                json.dump(original_data, f)

        # Carregar dados do JSON original
        with open(original_json_path, "r") as f:
            original_data = json.load(f)

        # Comparar dados e criar um JSON com as diferenças
        differences = {}
        for coin, price_info in data.items():
            if coin in original_data:
                original_price = original_data[coin]["usd"]
                new_price = price_info["usd"]
                if original_price != new_price:
                    differences[coin] = {"original": original_price, "new": new_price}
            else:
                differences[coin] = {"original": None, "new": price_info["usd"]}

        # Retornar o JSON com as diferenças
        return differences
    else:
        return {"error": f"Falha na requisição: {response.status_code}"}


# Definindo os parâmetros da DAG
default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime(2024, 10, 26),  # Defina a data de início aqui
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

# Criando a DAG
with DAG(
    "coinmarket_extraction",
    default_args=default_args,
    description="Uma DAG para extrair dados de criptomoedas da CoinGecko a cada 10 minutos",
    schedule_interval="*/10 * * * *",  # a cada 10 minutos
) as dag:

    # Tarefa para buscar dados da CoinGecko
    start = EmptyOperator(task_id="start")
    fetch_data = PythonOperator(
        task_id="fetch_coin_data",
        python_callable=fetch_coin_data,
    )
    end = EmptyOperator(task_id="end")

    (start >> fetch_data >> end)
