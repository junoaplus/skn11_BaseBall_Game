import pandas as pd
import pymysql

# CSV 경로
csv_path = '/Users/hwangjunho/Desktop/encore_skn11/Project/skn11_BaseBall_Game/data/players_2024.csv'

# 데이터프레임 불러오기
df_hitters = pd.read_csv(csv_path)

# DB 연결
conn = pymysql.connect(
    host='localhost',
    user='root',
    password='030617',
    db='kbo_simulator',
    charset='utf8'
)

cursor = conn.cursor()

# 컬럼 이름 (Year 포함됨!)
columns = ['Rank', 'Name', 'Team', 'Year', 'WAR', 'PA', 'AVG', 'OBP', 'SLG', 'OPS', 'WPA', 'spAVG', 'spOBP', 'spSLG', 'spOPS']

# SQL 쿼리 구성
sql = f"""
    INSERT INTO hitters ({', '.join(columns)})
    VALUES ({', '.join(['%s'] * len(columns))})
"""

# 데이터 삽입
for _, row in df_hitters.iterrows():
    values = tuple(row[col] for col in columns)  # ✅ 이 부분이 핵심!
    cursor.execute(sql, values)

# 커밋 및 연결 종료
conn.commit()
cursor.close()
conn.close()
