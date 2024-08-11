#!/usr/bin/env python3
# _*_ coding:utf-8 _*_
# Author : Noth
# Time : 2024-8-11
import requests
from bs4 import BeautifulSoup
import os, sys
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from telegram import Bot
import schedule
import time
import asyncio

chrome_options = Options()
chrome_options.add_argument('--ignore-certificate-errors') #忽略 SSL 證書錯誤選項
chrome_options.add_argument('--ignore-ssl-errors') #忽略 SSL 證書錯誤選項

# 配置 Telegram Token 以及自己的 Chat_ID
Telegram_token = '6457005566:AAGPrMMEcndcNmXxO_ElGQEVPZeDbef40hk'
Chat_id = '506336672'

# 配置 ChromeDriver 路徑
chrome_driver_path = r"C:\Users\No_tH\Desktop\chromedriver-win64\chromedriver.exe"
service = Service(chrome_driver_path)

# 初始化 ChromeDriver
print("Initializing ChromeDriver...")
driver = webdriver.Chrome(service=service, options=chrome_options)

# 初始化 Telegram Bot
bot = Bot(token=Telegram_token)

# ZD_ID文件路徑
processed_ids_file = "C:\\Users\\No_tH\\Desktop\\processed_ids.txt"

def load_processed_ids():
    """加载已處理的漏洞 ID"""
    if os.path.exists(processed_ids_file):
        with open(processed_ids_file, "r") as file:
            return set(file.read().splitlines())
    return set()

def save_processed_ids(processed_ids):
    """保存新的漏洞 ID"""
    with open(processed_ids_file, "w") as file:
        file.write("\n".join(processed_ids))

async def scrape_and_notify():
    url = 'https://zeroday.hitcon.org/vulnerability/disclosed'

    # 使用 Chrome 瀏覽器
    driver.get(url)

    # 等待頁面上的特定元素載入完成，最長等待時間為5秒
    try:
        element = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CLASS_NAME, "title tx-overflow-ellipsis"))
        )
    finally:
        # 打印頁面内容
        page_code = driver.page_source

        # 利用 BeautifulSoup 解析原始碼
        soup = BeautifulSoup(page_code, 'html.parser')
        titles = soup.find_all('h4', class_='title tx-overflow-ellipsis') #titles列表
        # 加载已處理的漏洞 ID
        
        processed_ids = load_processed_ids()
        new_ids = set()

        base_url = 'https://zeroday.hitcon.org'

        for h4 in titles:
            # 提取 <a> 標籤中的鏈接和文本
            link = h4.find('a')['href']
            full_link = base_url + link  # 拼接完整的链接
            text = h4.find('a').get_text()
            ZD_id = link.split('/')[-1] #提取鏈結的最後一部份(即ZD編號)

            #如果抓取的ZD_id重複即跳過
            if ZD_id in processed_ids:
                print(f"Skipping {ZD_id} (already processed)")
                continue
            message = f"{ZD_id}, 標題: {text}\n {full_link}"
            print(f"Sending message: {message}")
            await bot.send_message(chat_id=Chat_id, text=message)
            
            # 紀錄新抓取的 ID
            new_ids.add(ZD_id)
        
        driver.quit()
        
        # 保存新的漏洞 ID
        processed_ids.update(new_ids)
        save_processed_ids(processed_ids)

def run_scrape_and_notify():
    asyncio.run(scrape_and_notify())

# 調用主函式進行測試
run_scrape_and_notify()
exit()
