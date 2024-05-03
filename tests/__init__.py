import random

from requests import get
from concurrent.futures import ThreadPoolExecutor

url = 'http://localhost:8000/process_text'
with ThreadPoolExecutor() as executor:
    future = []
    for _ in range(400):
        future.append(executor.submit(get, url=url, params={'text': '啊啊啊' * random.randint(5, 30)}))
    executor.shutdown()
