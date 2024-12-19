import random

from requests import get
from concurrent.futures import ThreadPoolExecutor

url = 'http://localhost:8000/process_text'
with ThreadPoolExecutor() as executor:
    future = []
    for _ in range(60):
        future.append(executor.submit(get, url=url, params={'text': '啊' * random.randint(1, 30)}))
    executor.shutdown()
print(get('http://localhost:8000/get_usage').text)