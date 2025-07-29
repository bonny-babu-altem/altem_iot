from requests import Response, get
from datetime import datetime


def get_device_status(ip: str) -> str:
    endpoint: str = f'http://{ip}:5000/current'

    try:
        response: Response = get(endpoint, timeout=5)
        response.raise_for_status()
        return response.text

    except Exception as e:
        print(f"{datetime.now()} | Error occurred: {e}")
        raise e
