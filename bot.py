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
from bs4 import BeautifulSoup

# 配置 Telegram Token 以及自己的 Chat_ID
Telegram_token = '6457005566:AAGPrMMEcndcNmXxO_ElGQEVPZeDbef40hk'
chat_ids_file = "C:\\Users\\No_tH\\Desktop\\chat_ids.txt"

# 初始化 Telegram Bot
application = Application.builder().token(Telegram_token).build()

def load_chat_ids():
    """加载所有用户的 Chat ID"""
    if os.path.exists(chat_ids_file):
        with open(chat_ids_file, "r") as file:
            return set(file.read().splitlines())
    return set()

def save_chat_id(chat_id):
    """保存新的用户 Chat ID"""
    chat_ids = load_chat_ids()
    if chat_id not in chat_ids:
        with open(chat_ids_file, "a") as file:
            file.write(f"{chat_id}\n")

def load_processed_ids():
    """加载已處理的漏洞 ID"""
    processed_ids_file = "C:\\Users\\No_tH\\Desktop\\processed_ids.txt"
    if os.path.exists(processed_ids_file):
        with open(processed_ids_file, "r") as file:
            return set(file.read().splitlines())
    return set()

def save_processed_ids(processed_ids):
    """保存新的漏洞 ID"""
    processed_ids_file = "C:\\Users\\No_tH\\Desktop\\processed_ids.txt"
    with open(processed_ids_file, "w") as file:
        file.write("\n".join(processed_ids))

async def scrape_and_notify():
    # 配置 ChromeDriver 路徑
    chrome_driver_path = r"C:\Users\No_tH\Desktop\chromedriver-win64\chromedriver.exe"
    service = Service(chrome_driver_path)

    chrome_options = Options()
    chrome_options.add_argument('--ignore-certificate-errors')  # 忽略 SSL 證書錯誤選項
    chrome_options.add_argument('--ignore-ssl-errors')          # 忽略 SSL 證書錯誤選項

    # 初始化 ChromeDriver
    print("Initializing ChromeDriver...")
    driver = webdriver.Chrome(service=service, options=chrome_options)

    url = 'https://zeroday.hitcon.org/vulnerability/disclosed'
    driver.get(url)

    try:
        element = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CLASS_NAME, "title tx-overflow-ellipsis"))
        )
    finally:
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

            chat_ids = load_chat_ids()
            for chat_id in chat_ids:
                await application.bot.send_message(chat_id=chat_id, text=message)

            new_ids.add(ZD_id)

        driver.quit()
        processed_ids.update(new_ids)
        save_processed_ids(processed_ids)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理 /start 命令，保存用户 Chat ID 并抓取漏洞"""
    chat_id = str(update.message.chat_id)
    save_chat_id(chat_id)
    await context.bot.send_message(chat_id=chat_id, text="You have been subscribed to ZD notifications!")
    
    # 触发漏洞抓取并通知
    await scrape_and_notify()

# 添加处理 /start 命令的处理器
start_handler = CommandHandler('start', start)
application.add_handler(start_handler)

# 启动 Bot
application.run_polling()

def run_scrape_and_notify():
    asyncio.run(scrape_and_notify())

# 调用主函数进行测试
run_scrape_and_notify()
exit()
