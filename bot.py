#!/usr/bin/env python3
# _*_ coding:utf-8 _*_
# Author : Noth
# Time : 2024-8-11

# 從 Telegram 套件中匯入必要的類別
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# 匯入 Python 標準庫模組和第三方庫
import os, sys
import asyncio
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

# 配置 Telegram Token 以及用戶的 Chat_ID 檔案路徑
Telegram_token = '6457005566:AAGPrMMEcndcNmXxO_ElGQEVPZeDbef40hk'  # 這是 Bot 的 API Token
chat_ids_file = "C:\\Users\\No_tH\\Desktop\\chat_ids.txt"  # 儲存用戶 Chat ID 的檔案路徑

# 初始化 Telegram Bot
application = Application.builder().token(Telegram_token).build()

def load_chat_ids():
    """加載所有用戶的 Chat ID"""
    if os.path.exists(chat_ids_file):
        with open(chat_ids_file, "r") as file:
            return set(file.read().splitlines())  # 將所有 Chat ID 作為集合返回，以避免重複
    return set()

def save_chat_id(chat_id):
    """保存新的用戶 Chat ID"""
    chat_ids = load_chat_ids()  # 加載已有的 Chat ID
    if chat_id not in chat_ids:  # 如果 Chat ID 是新的，將其添加到檔案中
        with open(chat_ids_file, "a") as file:
            file.write(f"{chat_id}\n")

def load_processed_ids():
    """加載已處理的漏洞 ID"""
    processed_ids_file = "C:\\Users\\No_tH\\Desktop\\processed_ids.txt"
    if os.path.exists(processed_ids_file):
        with open(processed_ids_file, "r") as file:
            return set(file.read().splitlines())  # 返回已處理的漏洞 ID 集合
    return set()

def save_processed_ids(processed_ids):
    """保存新的漏洞 ID"""
    processed_ids_file = "C:\\Users\\No_tH\\Desktop\\processed_ids.txt"
    with open(processed_ids_file, "w") as file:
        file.write("\n".join(processed_ids))  # 將新的漏洞 ID 集合寫入檔案

async def scrape_and_notify():
    """抓取漏洞信息並通過 Telegram Bot 推送通知"""
    
    # 配置 ChromeDriver 路徑
    chrome_driver_path = r"C:\Users\No_tH\Desktop\chromedriver-win64\chromedriver.exe"
    service = Service(chrome_driver_path)

    # 配置 Chrome 瀏覽器選項
    chrome_options = Options()
    chrome_options.add_argument('--ignore-certificate-errors')  # 忽略證書錯誤
    chrome_options.add_argument('--ignore-ssl-errors')          # 忽略 SSL 錯誤

    # 初始化 ChromeDriver
    print("Initializing ChromeDriver...")
    driver = webdriver.Chrome(service=service, options=chrome_options)

    # 打開漏洞披露頁面
    url = 'https://zeroday.hitcon.org/vulnerability/disclosed'
    driver.get(url)

    try:
        # 等待頁面加載，直到找到指定的元素
        element = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CLASS_NAME, "title tx-overflow-ellipsis"))
        )
    finally:
        # 獲取頁面源代碼並使用 BeautifulSoup 進行解析
        page_code = driver.page_source
        soup = BeautifulSoup(page_code, 'html.parser')
        titles = soup.find_all('h4', class_='title tx-overflow-ellipsis')  # 查找所有包含漏洞信息的標籤
        
        # 加載已處理的漏洞 ID
        processed_ids = load_processed_ids()
        new_ids = set()

        base_url = 'https://zeroday.hitcon.org'

        # 遍歷所有抓取到的漏洞信息
        for h4 in titles:
            link = h4.find('a')['href']  # 獲取漏洞詳情頁面鏈接
            full_link = base_url + link  # 拼接完整的鏈接
            text = h4.find('a').get_text()  # 獲取漏洞標題
            ZD_id = link.split('/')[-1]  # 提取漏洞 ID

            if ZD_id in processed_ids:
                print(f"Skipping {ZD_id} (already processed)")  # 如果漏洞 ID 已處理，跳過
                continue
            message = f"{ZD_id}, 標題: {text}\n {full_link}"
            print(f"Sending message: {message}")

            chat_ids = load_chat_ids()  # 加載所有訂閱的用戶 Chat ID
            for chat_id in chat_ids:
                # 發送漏洞信息給所有訂閱的用戶
                await application.bot.send_message(chat_id=chat_id, text=message)

            new_ids.add(ZD_id)  # 將新處理的漏洞 ID 添加到集合中

        driver.quit()  # 關閉瀏覽器
        processed_ids.update(new_ids)  # 更新處理過的漏洞 ID 集合
        save_processed_ids(processed_ids)  # 保存新的漏洞 ID

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """處理 /start 命令，保存用戶 Chat ID 並抓取漏洞"""
    chat_id = str(update.message.chat_id)  # 獲取用戶的 Chat ID
    save_chat_id(chat_id)  # 保存用戶的 Chat ID
    await context.bot.send_message(chat_id=chat_id, text="You have been subscribed to ZD notifications!")
    
    # 觸發漏洞抓取並通知
    await scrape_and_notify()

# 添加處理 /start 命令的處理器
start_handler = CommandHandler('start', start)
application.add_handler(start_handler)

# 啟動 Bot，開始監聽消息
application.run_polling()

def run_scrape_and_notify():
    asyncio.run(scrape_and_notify())  # 運行漏洞抓取和通知的異步函數

# 調用主函數進行測試
run_scrape_and_notify()
exit()
