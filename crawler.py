print("===== START SCRIPT =====")

import requests
import time
import random
from bs4 import BeautifulSoup
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
from zoneinfo import ZoneInfo

import os
import json

scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

service_account_info = json.loads(os.environ["SERVICEACCOUNT"])

creds = Credentials.from_service_account_info(
    service_account_info,
    scopes=scope
)

client = gspread.authorize(creds)

# 관리 시트
manager = client.open_by_key("1j3o1y182r4vXN5oyfmV4QbtvkCkPbmnuMtRWAQFGQlM").sheet1
rows = manager.get_all_values()

now = datetime.now(ZoneInfo("Asia/Seoul"))
today = f"{now.month}/{now.day}"
print("현재 한국시간:", now)

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
}

for row in rows[1:]:

    keyword = row[0]
    if not keyword:
        continue

    urls = [u.strip() for u in row[1].split(",")]
    sheet_id = row[2]
    sheet_name = row[3]

    search_url = f"https://search.naver.com/search.naver?query={keyword}"

    res = requests.get(search_url, headers=headers)
    time.sleep(random.uniform(2,4))
    soup = BeautifulSoup(res.text, "html.parser")

    items = soup.select('[data-template-id="ugcItem"]')

    rank_list = []

    for i, item in enumerate(items, start=1):
        for url in urls:
            if url in str(item):
                rank_list.append(i)

    rank = min(rank_list) if rank_list else "-"
    
    print(keyword, "순위:", rank)

    

    # 결과 시트 열기
    result_spreadsheet = client.open_by_key(sheet_id)
    sheet = result_spreadsheet.worksheet(sheet_name)

    sheet_data = sheet.get_all_values()

    # 날짜 찾기
    date_row = None
    date_col = None

    for r, row_data in enumerate(sheet_data):
        for c, val in enumerate(row_data):
            if val == today:
                date_row = r + 1
                date_col = c + 1
                break
        if date_col:
            break

    if date_col is None:
        print("오늘 날짜 없음:", today)
        continue

    # 오전 / 오후 판단
    if now.hour < 12:
        write_col = date_col
    else:
        write_col = date_col + 1

    # 키워드 행 찾기 (C열)
    keyword_row = None

    for i, row_data in enumerate(sheet_data):
        if len(row_data) >= 3 and row_data[2] == keyword:
            keyword_row = i + 1
            break

    if keyword_row is None:
        print("키워드 행 없음:", keyword)
        continue

    # 순위 기록
    sheet.update_cell(keyword_row, write_col, rank)

    print("기록 완료\n")