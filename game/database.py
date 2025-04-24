import pandas as pd
import pymysql
import random


def get_team_schedule(team_name):
    conn = pymysql.connect(host='localhost', user='root', password='030617', db='kbo_simulator', charset='utf8')
    query = f"""
    SELECT * FROM schedule
    WHERE `Seoul Jamsil` LIKE '%%{team_name}%%'
       OR `Seoul Gocheok` LIKE '%%{team_name}%%'
       OR `Incheon Munhak` LIKE '%%{team_name}%%'
       OR Suwon LIKE '%%{team_name}%%'
       OR Daejeon LIKE '%%{team_name}%%'
       OR Daegu LIKE '%%{team_name}%%'
       OR Gwangju LIKE '%%{team_name}%%'
       OR `Busan Sajik` LIKE '%%{team_name}%%'
       OR Changwon LIKE '%%{team_name}%%'
    ORDER BY Date
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df


def update_player_stats(team_name, lineup, pitcher_name):
    conn = pymysql.connect(host='localhost', user='root', password='030617', db='kbo_simulator', charset='utf8')
    cur = conn.cursor()
    # 타자 기록 업데이트
    for batter in lineup:
        ab = random.randint(3,5)
        hits = random.randint(0,ab)
        rbi = random.randint(0,3)
        hr = 1 if random.random() < 0.1 else 0
        runs = random.randint(0,2)
        cur.execute(
            """
            INSERT INTO virtual_hitters (player_name, team, games_played, at_bats, hits, rbi, homeruns, runs)
            VALUES (%s, %s, 1, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                games_played = games_played + 1,
                at_bats = at_bats + VALUES(at_bats),
                hits = hits + VALUES(hits),
                rbi = rbi + VALUES(rbi),
                homeruns = homeruns + VALUES(homeruns),
                runs = runs + VALUES(runs)
            """,
            (batter, team_name, ab, hits, rbi, hr, runs)
        )
    # 투수 기록 업데이트
    innings = round(random.uniform(4,7), 1)
    er = random.randint(0,4)
    so = random.randint(1,6)
    bb = random.randint(0,3)
    win = 1 if random.random() < 0.5 else 0
    loss = 1 - win
    save = 1 if innings < 2 and win else 0
    cur.execute(
        """
        INSERT INTO virtual_pitchers (player_name, team, games_played, innings, earned_runs, strikeouts, walks, wins, losses, saves)
        VALUES (%s, %s, 1, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            games_played = games_played + 1,
            innings = innings + VALUES(innings),
            earned_runs = earned_runs + VALUES(earned_runs),
            strikeouts = strikeouts + VALUES(strikeouts),
            walks = walks + VALUES(walks),
            wins = wins + VALUES(wins),
            losses = losses + VALUES(losses),
            saves = saves + VALUES(saves)
        """,
        (pitcher_name, team_name, innings, er, so, bb, win, loss, save)
    )
    conn.commit()
    cur.close()
    conn.close()


def update_team_winloss(team_name, result="win"):
    conn = pymysql.connect(host='localhost', user='root', password='030617', db='kbo_simulator', charset='utf8')
    cur = conn.cursor()
    if result == "win":
        cur.execute(
            """
            INSERT INTO virtual_rankings (team_name, games, wins, losses, draws)
            VALUES (%s, 1, 1, 0, 0)
            ON DUPLICATE KEY UPDATE
                games = games + 1,
                wins = wins + 1
            """,
            (team_name,)
        )
    else:
        cur.execute(
            """
            INSERT INTO virtual_rankings (team_name, games, wins, losses, draws)
            VALUES (%s, 1, 0, 1, 0)
            ON DUPLICATE KEY UPDATE
                games = games + 1,
                losses = losses + 1
            """,
            (team_name,)
        )
    conn.commit()
    cur.close()
    conn.close()


def update_virtual_rankings():
    conn = pymysql.connect(host='localhost', user='root', password='030617', db='kbo_simulator', charset='utf8')
    cur = conn.cursor()
    cur.execute(
        "UPDATE virtual_rankings SET win_rate = CASE WHEN games>0 THEN ROUND(wins/games,3) ELSE 0 END"
    )
    conn.commit()
    cur.close()
    conn.close()