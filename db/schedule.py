import pandas as pd
import pymysql
from datetime import datetime

# CSV 불러오기
df = pd.read_csv('/Users/hwangjunho/Desktop/encore_skn11/Project/skn11_BaseBall_Game/data/schedule_2024.csv')

# 날짜 변환 함수
def convert_to_date(row):
    try:
        month = int(row['Date'])
        day = int(float(row['Day']))
        return datetime(2024, month, day).strftime('%Y-%m-%d')
    except:
        return None

# 날짜 컬럼 추가
df['FullDate'] = df.apply(convert_to_date, axis=1)

# 💡 NaN → None으로 안전하게 변환
df = df.astype(object).where(pd.notnull(df), None)

# DB 연결
conn = pymysql.connect(
    host='localhost',
    user='root',
    password='030617',
    db='kbo_simulator',
    charset='utf8'
)
cursor = conn.cursor()

# SQL 준비
insert_sql = """
INSERT INTO schedule (
    Date, Day, Weekday, `Seoul Jamsil`, `Seoul Gocheok`, `Incheon Munhak`, Suwon,
    Daejeon, Daegu, Gwangju, `Busan Sajik`, Changwon
) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
"""

# 삽입
for _, row in df.iterrows():
    cursor.execute(insert_sql, (
        row['FullDate'],
        row['Day'],
        row['Weekday'],
        row['Seoul Jamsil'],
        row['Seoul Gocheok'],
        row['Incheon Munhak'],
        row['Suwon'],
        row['Daejeon'],
        row['Daegu'],
        row['Gwangju'],
        row['Busan Sajik'],
        row['Changwon']
    ))

conn.commit()
cursor.close()
conn.close()
