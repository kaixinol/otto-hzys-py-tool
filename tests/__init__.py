from requests import get
from concurrent.futures import ThreadPoolExecutor

url = 'http://localhost:8892/process_text'
params = {'text': '啊啊啊'*4}

with ThreadPoolExecutor() as executor:
    future =[]
    for _ in range(40):
        future.append(executor.submit(get, url=url, params=params))
    executor.shutdown()
