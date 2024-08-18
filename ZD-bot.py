#!/usr/bin/env python3  
# _*_ coding:utf-8 _*_
# Author : Noth
# Time : 2024-8-11

from telegram import Update  # 從 Telegram 庫導入 Update 模塊
from telegram.ext import Application, CommandHandler, ContextTypes  # 從 Telegram 庫導入應用程序、命令處理程序、上下文類型
import os, sys  # 導入 os 和 sys 模塊，用於文件操作和系統交互
import asyncio  # 導入 asyncio 模塊，用於非同步處理
from selenium import webdriver  # 從 Selenium 庫導入 webdriver，用於自動化網頁操作
from selenium.webdriver.chrome.service import Service  # 導入 Service 類，用於 ChromeDriver 的服務管理
from selenium.webdriver.chrome.options import Options  # 導入 Options 類，用於配置 ChromeDriver 的啟動選項
from selenium.webdriver.common.by import By  # 從 Selenium 庫導入 By 類，用於定位元素
from selenium.webdriver.support.ui import WebDriverWait  # 導入 WebDriverWait，用於顯式等待
from selenium.webdriver.support import expected_conditions as EC  # 導入 expected_conditions，定義元素等待條件
from selenium.common.exceptions import TimeoutException  # 從 Selenium 庫導入 TimeoutException，用於處理超時異常
from bs4 import BeautifulSoup  # 從 BeautifulSoup 庫導入 BeautifulSoup，用於解析 HTML 網頁內容
from webdriver_manager.chrome import ChromeDriverManager  # 從 webdriver_manager 庫導入 ChromeDriverManager，自動管理 ChromeDriver

# 配置 Telegram Token 以及群組 ID (-4101931565)
Telegram_token = '修改Token值'  # Telegram Bot 的 API Token，需要替換為實際的 Token 值
group_id = -4101931565  # 指定 Telegram 群組的 ID，將訊息發送到此群組

# 初始化 Telegram Bot
application = Application.builder().token(Telegram_token).build()  # 創建 Telegram 應用程序實例，並使用提供的 Token 進行初始化

def load_processed_ids():
    """加載已處理的漏洞 ID"""
    processed_ids_file = "C:\\Users\\xxxx\\Desktop\\processed_ids.txt"  # 指定存儲已處理漏洞 ID 的文件路徑
    if os.path.exists(processed_ids_file):  # 檢查該文件是否存在
        with open(processed_ids_file, "r") as file:  # 如果文件存在，打開文件進行讀取
            return set(file.read().splitlines())  # 讀取文件內容並將每行轉換為一個集合返回
    return set()  # 如果文件不存在，返回一個空的集合

def save_processed_ids(processed_ids):
    """保存新的漏洞 ID"""
    processed_ids_file = "C:\\Users\\xxxx\\Desktop\\processed_ids.txt"  # 指定存儲已處理漏洞 ID 的文件路徑
    with open(processed_ids_file, "w") as file:  # 打開文件進行寫入（如果文件不存在將自動創建）
        file.write("\n".join(processed_ids))  # 將集合中的每個 ID 寫入文件，每個 ID 占一行

async def scrape_and_notify():
    # 配置 ChromeDriver 路徑
    chrome_options = Options()  # 創建 ChromeDriver 選項的實例
    chrome_options.add_argument('--ignore-certificate-errors')  # 忽略 SSL 證書錯誤選項
    chrome_options.add_argument('--ignore-ssl-errors')  # 忽略 SSL 證書錯誤選項

    # 初始化 ChromeDriver
    print("Initializing ChromeDriver...")  # 在終端打印初始化信息
    service = Service(ChromeDriverManager().install())  # 使用 ChromeDriverManager 安裝和管理 ChromeDriver，並啟動服務
    driver = webdriver.Chrome(service=service, options=chrome_options)  # 創建 Chrome 瀏覽器的 WebDriver 實例

    url = 'https://zeroday.hitcon.org/vulnerability/disclosed'  # 目標網站的 URL 地址
    driver.get(url)  # 使用 WebDriver 進入目標 URL

    try:
        element = WebDriverWait(driver, 10).until(  # 設置顯式等待，最多等待 10 秒
            EC.presence_of_element_located((By.CLASS_NAME, "title tx-overflow-ellipsis"))  # 等待 class 為 "title tx-overflow-ellipsis" 的元素出現
        )
    except TimeoutException:
        # 忽略超時錯誤，繼續執行代碼
        print("Timeout occurred, but continuing...")  # 如果超時，打印信息但不影響後續代碼執行
        pass  # 繼續執行

    try:
        page_code = driver.page_source  # 獲取當前頁面的 HTML 源代碼
        soup = BeautifulSoup(page_code, 'html.parser')  # 使用 BeautifulSoup 解析 HTML 源代碼
        titles = soup.find_all('h4', class_='title tx-overflow-ellipsis')  # 查找所有 class 為 "title tx-overflow-ellipsis" 的 h4 標題元素
        
        processed_ids = load_processed_ids()  # 加載已處理的漏洞 ID
        new_ids = set()  # 創建一個空集合來存儲新發現的漏洞 ID

        base_url = 'https://zeroday.hitcon.org'  # 定義基礎 URL，用於拼接完整的漏洞連結

        for h4 in titles:  # 遍歷所有的標題元素
            link = h4.find('a')['href']  # 提取 h4 元素中的鏈接
            full_link = base_url + link  # 拼接成完整的 URL
            text = h4.find('a').get_text()  # 提取標題文本
            ZD_id = link.split('/')[-1]  # 從鏈接中提取漏洞 ID

            if ZD_id in processed_ids:  # 檢查這個漏洞 ID 是否已經處理過
                print(f"Skipping {ZD_id} (already processed)")  # 如果已經處理過，打印信息並跳過
                continue  # 繼續下一個循環
            message = f"{ZD_id}, 標題: {text}\n {full_link}"  # 構建發送到 Telegram 的訊息內容
            print(f"Sending message: {message}")  # 打印正在發送的訊息

            # 將消息發送到指定的群組
            await application.bot.send_message(chat_id=group_id, text=message)  # 使用 Telegram Bot 將消息發送到指定的群組

            new_ids.add(ZD_id)  # 將新發現的漏洞 ID 加入新集合

        processed_ids.update(new_ids)  # 更新已處理的漏洞 ID 集合
        save_processed_ids(processed_ids)  # 保存新的已處理漏洞 ID 集合到文件
    except Exception as e:  # 捕獲任意異常
        print(f"An error occurred during processing: {e}")  # 打印異常信息
    finally:
        driver.quit()  # 無論是否出錯，最終都關閉 WebDriver

if __name__ == "__main__":  # 如果該文件是作為主程式運行
    # 如果你只想執行一次爬取任務並退出
    asyncio.run(scrape_and_notify())  # 使用 asyncio 執行非同步爬取並發送通知的任務
    sys.exit(0)  # 明確退出程序，返回 0 表示正常退出
