#!/usr/bin/env python3
# _*_ coding:utf-8 _*_
# Author : Noth
# Time : 2024-8-11

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import os, sys
import asyncio
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException  # 導入 TimeoutException
from bs4 import BeautifulSoup
from webdriver_manager.chrome import ChromeDriverManager

# 配置 Telegram Token 以及群組 ID (-4101931565)
Telegram_token = '更改'
group_id = -4101931565  # 指定群組 ID

# 初始化 Telegram Bot
application = Application.builder().token(Telegram_token).build()

def load_processed_ids():
    """加載已處理的漏洞 ID"""
    processed_ids_file = "C:\\Users\\T124375136\\Desktop\\processed_ids.txt"
    if os.path.exists(processed_ids_file):
        with open(processed_ids_file, "r") as file:
            return set(file.read().splitlines())
    return set()

def save_processed_ids(processed_ids):
    """保存新的漏洞 ID"""
    processed_ids_file = "C:\\Users\\T124375136\\Desktop\\processed_ids.txt"
    with open(processed_ids_file, "w") as file:
        file.write("\n".join(processed_ids))

async def scrape_and_notify():
    # 配置 ChromeDriver 路徑
    chrome_options = Options()
    chrome_options.add_argument('--ignore-certificate-errors')  # 忽略 SSL 證書錯誤選項
    chrome_options.add_argument('--ignore-ssl-errors')          # 忽略 SSL 證書錯誤選項

    # 初始化 ChromeDriver
    print("Initializing ChromeDriver...")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    url = 'https://zeroday.hitcon.org/vulnerability/disclosed'
    driver.get(url)

    try:
        element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "title tx-overflow-ellipsis"))
        )
    except TimeoutException:
        # 忽略超時錯誤，繼續執行代碼
        print("Timeout occurred, but continuing...")
        pass

    try:
        page_code = driver.page_source
        soup = BeautifulSoup(page_code, 'html.parser')
        titles = soup.find_all('h4', class_='title tx-overflow-ellipsis')
        
        processed_ids = load_processed_ids()
        new_ids = set()

        base_url = 'https://zeroday.hitcon.org'

        for h4 in titles:
            link = h4.find('a')['href']
            full_link = base_url + link
            text = h4.find('a').get_text()
            ZD_id = link.split('/')[-1]

            if ZD_id in processed_ids:
                print(f"Skipping {ZD_id} (already processed)")
                continue
            message = f"{ZD_id}, 標題: {text}\n {full_link}"
            print(f"Sending message: {message}")

            # 將消息發送到指定的群組
            await application.bot.send_message(chat_id=group_id, text=message)

            new_ids.add(ZD_id)

        processed_ids.update(new_ids)
        save_processed_ids(processed_ids)
    except Exception as e:
        print(f"An error occurred during processing: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    # 如果你只想執行一次爬取任務並退出
    asyncio.run(scrape_and_notify())
    sys.exit(0)  # 明確退出程序
