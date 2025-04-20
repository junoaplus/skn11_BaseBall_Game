# crawlers/crawl_players.py

import os
import pandas as pd
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def crawl_players(driver):
    print("▶ 타자 기록 수집 시작")
    url = "http://www.statiz.co.kr/stat.php?opt=1&sopt=0&re=0&ys=2024&ye=2024&se=0&pa=0"
    driver.get(url)
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, "table"))
    )
    tables = pd.read_html(driver.page_source)
    for table in tables:
        if '이름' in table.columns and '타율' in table.columns:
            players = table
            break
    else:
        print("❌ 선수 기록 테이블을 찾지 못했습니다.")
        return

    players = players.rename(columns={'득점권': '찬스타율'}) if '득점권' in players.columns else players
    cols = ['이름', '팀', '포지션', '타율', '찬스타율', '도루', '도루성공률']
    cols = [c for c in cols if c in players.columns]
    players = players[cols]

    os.makedirs("data", exist_ok=True)
    players.to_csv("data/players_2024.csv", index=False)
    print("✅ players_2024.csv 저장 완료")

if __name__ == "__main__":
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    driver = webdriver.Chrome(options=options)

    crawl_players(driver)
    driver.quit()
