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
from fastapi.responses import StreamingResponse, JSONResponse
from loguru import logger
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from .browser import get_multiple_browsers

app = FastAPI(debug=True)

sem = asyncio.Semaphore(os.cpu_count() // 2)


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
async def get_usage():
    browser_pid: list[int] = [_.service.process.pid for _ in global_browser]
    browser_process = [psutil.Process(_) for _ in browser_pid]
    memory_info = [_.memory_info() for _ in browser_process]
    total_browser_usage: int = sum(info.rss for info in memory_info)
    main_process_usage: int = psutil.Process(os.getpid()).memory_info().rss
    response_data = {
        "chrome": {
            "instances": len(global_browser),
            "memory_usage_gb": round(total_browser_usage / (1024 ** 3), 2)
        },
        "main_process": {
            "memory_usage_gb": round(main_process_usage / (1024 ** 3), 2)
        },
        "total_memory_usage_gb": round((total_browser_usage + main_process_usage) / (1024 ** 3), 2),
        "available_browser":  sum(1 for i in global_browser if not i.is_using)
    }

    return JSONResponse(content=response_data)

global_browser = get_multiple_browsers(os.cpu_count() // 2, True)
argv_url =[i for i in argv if 'http://' in i]
url ='http://localhost:8080/' if not argv_url else argv_url


def get_file_content_chrome(browser_: WebDriver):
    result = browser_.execute_script("""
const response = await fetch(window.ottoVoice);
const blob = await response.blob();
const arrayBuffer = await blob.arrayBuffer();
return Array.from(new Uint8Array(arrayBuffer));
""",)
    if type(result) is int:
        raise Exception(f"Request failed with status {result}")
    return bytes(result)


def get_available_browser():
    while all([i.is_using for i in global_browser]):
        sleep(random.randint(100, 300) / 1000)
    for i in global_browser:
        if not i.is_using:
            i.is_using = True
            return i


def convert_text_to_voice(text: str):
    browser_one = get_available_browser()
    try:
        if browser_one.current_url != url:
            browser_one.get(url)
        elem = browser_one.find_element(By.XPATH,
                                        "//textarea[contains(@class, 'el-textarea__inner')]")
        elem.clear()
        elem.send_keys(text)
        WebDriverWait(browser_one, 20).until(EC.element_to_be_clickable((By.XPATH,
                                                                         "//button[span[text() = '生成otto鬼叫']]"))).click()
        WebDriverWait(browser_one, 20).until(EC.element_to_be_clickable((By.XPATH,
                                                                         "//button[span[text() = '下载原音频']]"))).click()
        data = get_file_content_chrome(browser_one)
        logger.debug(f'{len(data) / (1024 * 1024): .2f}MB')
    finally:
        browser_one.is_using = False
    return data


uvicorn.run(app, host="localhost", port=8000)

