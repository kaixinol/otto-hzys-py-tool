import asyncio
import base64
import os
import random
import psutil
from io import BytesIO
from sys import argv
from time import sleep

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse, PlainTextResponse
from loguru import logger
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from .browser import get_multiple_browsers

app = FastAPI()

sem = asyncio.Semaphore(os.cpu_count() * 4)


@app.get("/process_text")
async def process_text(text: str):
    async with sem:
        if len(text) > 120:
            raise HTTPException(400)
        try:
            return StreamingResponse(BytesIO(await asyncio.to_thread(convert_text_to_voice, text)), media_type="audio/wav")
        except Exception as e:
            raise HTTPException(500, detail=str(e))


@app.get("/get_usage")
async def process_text():
    browser_pid = [_.service.process.pid for _ in global_browser]
    browser_process = [psutil.Process(_) for _ in browser_pid]
    memory_info = [_.memory_info() for _ in browser_process]
    total_usage: int = 0
    for i in memory_info:
        total_usage += i.rss
    return PlainTextResponse(
        f'''Chrome ({len(global_browser)}): {total_usage / (pow(1024, 3)): .2f}GB\nMain Process:{psutil.Process(os.getpid()).memory_info().rss / pow(1024, 3): .2f}GB''')


global_browser = get_multiple_browsers(os.cpu_count(), True)


def get_file_content_chrome(browser_: WebDriver, uri):
    result = browser_.execute_async_script("""
    let uri = arguments[0];
    let callback = arguments[1];
    let toBase64 = function(buffer){for(var r,n=new Uint8Array(buffer),t=n.length,a=new Uint8Array(4*Math.ceil(t/3)),i=new Uint8Array(64),o=0,c=0;64>c;++c)i[c]="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/".charCodeAt(c);for(c=0;t-t%3>c;c+=3,o+=4)r=n[c]<<16|n[c+1]<<8|n[c+2],a[o]=i[r>>18],a[o+1]=i[r>>12&63],a[o+2]=i[r>>6&63],a[o+3]=i[63&r];return t%3===1?(r=n[t-1],a[o]=i[r>>2],a[o+1]=i[r<<4&63],a[o+2]=61,a[o+3]=61):t%3===2&&(r=(n[t-2]<<8)+n[t-1],a[o]=i[r>>10],a[o+1]=i[r>>4&63],a[o+2]=i[r<<2&63],a[o+3]=61),new TextDecoder("ascii").decode(a)};
    let xhr = new XMLHttpRequest();
    xhr.responseType = 'arraybuffer';
    xhr.onload = function(){ callback(toBase64(xhr.response)) };
    xhr.onerror = function(){ callback(xhr.status) };
    xhr.open('GET', uri);
    xhr.send();
    """, uri)
    if type(result) is int:
        raise Exception(f"Request failed with status {result}")
    return base64.b64decode(result)


def get_available_browser():
    while all([i.__dict__['is_using'] for i in global_browser]):
        sleep(random.randint(100, 300) / 1000)
    for i in global_browser:
        if not i.__dict__['is_using']:
            i.__dict__['is_using'] = True
            return i


def convert_text_to_voice(text: str):
    browser_one = get_available_browser()
    try:
        url = [i for i in argv if 'http://' in i]
        browser_one.get(url[0] if url else 'http://localhost:8080/')
        elem = browser_one.find_element(By.XPATH,
                                        "//textarea[contains(@class, 'el-textarea__inner')]")
        elem.clear()
        elem.send_keys(text)
        WebDriverWait(browser_one, 20).until(EC.element_to_be_clickable((By.XPATH,
                                                                         "//button[span[text() = '生成otto鬼叫']]"))).click()
        WebDriverWait(browser_one, 20).until(EC.element_to_be_clickable((By.XPATH,
                                                                         "//button[span[text() = '下载原音频']]"))).click()
        data = get_file_content_chrome(browser_one, browser_one.execute_script('return window.ottoVoice'))
        logger.debug(f'{len(data) / (1024 * 1024): .2f}MB')
    finally:
        browser_one.__dict__['is_using'] = False
    return data


uvicorn.run(app, host="localhost", port=8000)
