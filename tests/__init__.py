import random

from requests import get
from concurrent.futures import ThreadPoolExecutor

url = 'http://localhost:8000/process_text'
with ThreadPoolExecutor() as executor:
    future = []
    for _ in range(60):
        future.append(executor.submit(get, url=url, params={'text': '啊啊啊' * random.randint(5, 20)}))
    executor.shutdown()
get('http://localhost:8000/get_usage')