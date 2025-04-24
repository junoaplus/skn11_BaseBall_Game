import pandas as pd
import pymysql

# CSV 경로
csv_path = '/Users/hwangjunho/Desktop/encore_skn11/Project/skn11_BaseBall_Game/data/players_P_2024.csv'

# 데이터프레임 불러오기
df_pitchers = pd.read_csv(csv_path)

# DB 연결
conn = pymysql.connect(
    host='localhost',
    user='root',
    password='030617',
    db='kbo_simulator',
    charset='utf8'
)

cursor = conn.cursor()

# 컬럼 명시 (총 16개)
columns = ['Rank', 'Name', 'Team', 'WAR', 'G', 'GS', 'IP', 'ERA', 'WHIP',
           'SO', 'BB', 'H', 'HR', 'WP', 'BK', 'SB']

# SQL 쿼리
sql = f"""
    INSERT INTO pitchers ({', '.join(columns)})
    VALUES ({', '.join(['%s'] * len(columns))})
"""

# 삽입
for _, row in df_pitchers.iterrows():
    values = tuple(row[col] for col in columns)
    cursor.execute(sql, values)

# 커밋 및 종료
conn.commit()
cursor.close()
conn.close()
