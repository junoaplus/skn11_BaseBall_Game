import pymysql
import pandas as pd


def select_team():
    teams = ['LG','KT','SSG','NC','두산','KIA','삼성','롯데','키움','한화']
    manager_id = input("👤 감독 아이디를 입력하세요: ")
    conn = pymysql.connect(host='localhost', user='root', password='030617', db='kbo_simulator', charset='utf8')
    cur = conn.cursor()
    cur.execute("SELECT team_name FROM user_team WHERE manager_id=%s", (manager_id,))
    row = cur.fetchone()
    if row:
        team = row[0]
        print(f"\n✅ 기존 감독입니다. '{team}' 팀으로 진행합니다!\n")
    else:
        print("\n🎯 팀을 선택하세요:")
        for i,t in enumerate(teams,1): print(f"{i}. {t}")
        choice = int(input("선택: "))
        team = teams[choice-1]
        cur.execute("INSERT INTO user_team(manager_id,team_name) VALUES(%s,%s)", (manager_id,team))
        conn.commit()
        print(f"\n✅ '{team}' 팀으로 시즌을 시작합니다!\n")
    cur.close()
    conn.close()
    return team


def select_lineup(team_name):
    conn = pymysql.connect(host='localhost', user='root', password='030617', db='kbo_simulator', charset='utf8')
    df_hit = pd.read_sql(f"SELECT Name FROM hitters WHERE Team='{team_name}' ORDER BY WAR DESC", conn)
    df_pt  = pd.read_sql(f"SELECT Name FROM pitchers WHERE Team='{team_name}' ORDER BY WAR DESC", conn)
    conn.close()

    print(f"\n📋 {team_name} 타자 후보 ({len(df_hit)}명):")
    for i,name in enumerate(df_hit['Name'],1): print(f"{i}. {name}")
    lineup = []
    while len(lineup) < 9:
        idx = int(input(f"👉 {len(lineup)+1}번 타자 선택 (1~{len(df_hit)}): "))
        name = df_hit['Name'][idx-1]
        if name not in lineup:
            lineup.append(name)
        else:
            print("⚠️ 이미 선택된 선수입니다.")
    bench = [n for n in df_hit['Name'] if n not in lineup]

    print(f"\n🧤 {team_name} 투수 후보 ({len(df_pt)}명):")
    for i,name in enumerate(df_pt['Name'],1): print(f"{i}. {name}")
    sp_idx = int(input("👉 선발 투수 선택: "))
    starter = df_pt['Name'][sp_idx-1]
    bullpen = [n for n in df_pt['Name'] if n != starter]

    print("\n✅ 최종 라인업:")
    for i,name in enumerate(lineup,1): print(f"{i}번 타자: {name}")
    print(f"선발 투수: {starter}\n불펜: {bullpen}\n벤치: {bench}\n")
    return lineup, bench, starter, bullpen