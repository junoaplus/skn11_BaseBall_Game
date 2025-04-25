import random
from game.database import (
    get_team_schedule,
    update_player_stats,
    update_team_winloss,
    update_virtual_rankings
)
from llm.game_runner import (
    get_team_stats,
    ask_roster,
    ask_pa_result,
    get_match_result_only,
    chance_result
)

STADIUMS = [
    'Seoul Jamsil','Seoul Gocheok','Incheon Munhak',
    'Suwon','Daejeon','Daegu','Gwangju','Busan Sajik','Changwon'
]

def process_pa_result(pa_result: str, runners: list, hit_streak: str):
    # 0) 따옴표·공백 제거, 소문자화
    pa = pa_result.strip().strip("'\"").lower()
    runs = 0
    out = 0
    a = -1
    
    if pa == 'chance':
        return out, runners , 100, hit_streak

    # 1) 아웃 상황 
    if pa in ('strikeout', 'groundout', 'flyout', 'pop out'):
        if pa == 'strikeout':
            print("삼진 아웃")
        elif pa == 'groundout':
            print("땅볼 아웃")
        elif pa == 'flyout':
            print("플라이 아웃")
        elif pa == 'pop out':
            print("파울 플라이 아웃")
        out = 1
        return out, runners, 0, hit_streak

    # 2) 출루/안타
    elif 'single' in pa:
        print("안타")
        hit_streak += 1
        runners = [1] + [r+1 for r in runners]
    elif 'double' in pa:
        print("2루타")
        hit_streak += 1
        runners = [2] + [r+2 for r in runners]
    elif 'triple' in pa:
        print("3루타")
        hit_streak += 1
        runners = [3] + [r+3 for r in runners]
    elif 'home run' in pa or 'homer' in pa:
        print("홈런")
        hit_streak += 1
        runs += len(runners) + 1
        runners = []
    elif pa == '홈런':
        print("홈런")
        hit_streak += 1
        runs += len(runners) + 1
        runners = []
    elif pa == "홈 런":
        print("홈런")
        hit_streak += 1
        runs += len(runners) + 1
        runners = []
    elif pa == "홈런 ":
        print("홈런")
        hit_streak += 1
        runs += len(runners) + 1
        runners = []
    elif 'base on balls' in pa or 'walk' in pa:
        print("볼넷")
        hit_streak += 1
        runners = [1] + [r+1 for r in runners]
    
    
    else:
        a = 0 
        if a == 0:
            print("삼진 아웃")
            out=1
            return out, runners, 0, hit_streak

    # 3) 베이스 초과 주자 득점 처리
    new_runners = []
    for r in runners:
        if r >= 4:
            runs += 1
        else:
            new_runners.append(r)
    return 0, new_runners, runs, hit_streak



def play_season(team_name, our_lineup, our_bench, our_starting, our_bullpen):
    # 우리 팀 스탯 로드
    our_hitters_df, our_pitchers_df = get_team_stats(team_name)
    sched_df = get_team_schedule(team_name)

    for _, game in sched_df.iterrows():
        game_date = game['Date']
        for stad in STADIUMS:
            cell = game.get(stad)
            if not isinstance(cell, str) or '-' not in cell:
                continue
            away, home = cell.split('-')
            if team_name not in (away, home):
                continue

            is_home = (team_name == home)
            opp_team = home if not is_home else away
            print(f"⚾ [{game_date}] {away} vs {home} @ {stad}")

            # 상대 로스터 생성
            opp_hitters_df, opp_pitchers_df = get_team_stats(opp_team)
            roster = ask_roster(opp_team, opp_hitters_df, opp_pitchers_df)
            opp_lineup   = roster['lineup']
            opp_bench    = roster['bench']
            opp_starting = roster['starting']
            opp_bullpen  = roster['bullpen']

            # 이닝/스코어 초기화
            inning, half, outs, runners = 1, 'top', 0, []
            score = {'home':0, 'away':0}
            our_idx, opp_idx = 0, 0
            chance_count = 0
            sc = 0
            max_chance   = random.randint(4,6)
            hit_streak = 0

            # 1~9회 PA 루프
            while inning <= 9:
                # 9회말 우리팀이 앞서면 종료
                if inning == 9 and half == 'top' and score['home'] > score['away']:
                    break

                # 공격·수비팀 결정
                if half == 'top':
                    atk_team, def_team = away, home
                else:
                    atk_team, def_team = home, away
                our_attack = (atk_team == team_name)

                # 라인업과 투수 결정
                if our_attack:
                    hitters_df, pitchers_df = our_hitters_df, opp_pitchers_df
                    atk_lineup, atk_idx = our_lineup, our_idx
                    def_pitcher = opp_starting
                else:
                    hitters_df, pitchers_df = opp_hitters_df, our_pitchers_df
                    atk_lineup, atk_idx = opp_lineup, opp_idx
                    def_pitcher = our_starting

                # 배터 선택 및 스탯 조회
                batter = atk_lineup[atk_idx]
                batter_stats = hitters_df.set_index('Name').loc[batter].to_dict()

                # ★ 여기서 def_pitcher가 dict/list면 이름만 뽑아오기
                if isinstance(def_pitcher, dict):
                    def_pitcher = def_pitcher.get('name') or next(iter(def_pitcher.values()))
                elif isinstance(def_pitcher, (list, tuple)):
                    def_pitcher = def_pitcher[0]

                pitcher_stats = pitchers_df.set_index('Name').loc[def_pitcher].to_dict()

                # 컨텍스트 생성
                context = {
                    'date': game_date.strftime('%Y-%m-%d'),
                    'stadium': stad,
                    'inning': inning,
                    'half': half,
                    'batter': batter,
                    'batter_stats': batter_stats,
                    'pitcher': def_pitcher,
                    'pitcher_stats': pitcher_stats,
                    'bench': our_bench if our_attack else opp_bench,
                    'bullpen': our_bullpen if not our_attack else opp_bullpen,
                    'outs': outs,
                    'runners': runners,
                    'score': score,
                    'chance_count': chance_count,
                    'max_chance': max_chance,
                    'our_attack': our_attack   
                }

                pa_result,hit_streak = ask_pa_result(context, sc, hit_streak)
                
                side_label = '초' if half == 'top' else '말'
                print(f"  ▶ {inning}회{side_label} {atk_idx+1}번타자 {atk_lineup[atk_idx]} 투수: {def_pitcher}")

                # PA 결과 처리
                outs_inc, runners, runs, hit_streak = process_pa_result(pa_result, runners, hit_streak)
                if runs == 100:
                    print("찬스 상황 입니다")
                    loc_score = {away: score['away'], home: score['home']}
                    print(f"아웃: {outs} 주자: {runners} 득점: {loc_score}")
                    print("어떤 판단을 내릴까요? 이유와 함계 이야기 해주세요")
                    print("ex) 홈런을 노리는 스윙을 한다 승기를 한번에 잡을 수 있는 기회 이고 타자는 홈런 타자이기 때문이다, 컨택 스윙을 한다 컨택이 좋은 타자이고 안타를 쳐서 차곡차곡 득점을 쌓아간다.")
                    player = input("판단을 내려 주세요: ")
                    context = {
                        'date': game_date,
                        'stadium': stad,
                        'inning': inning,
                        'half': half,
                        'batter': batter,
                        'batter_stats': batter_stats,
                        'pitcher': def_pitcher,
                        'pitcher_stats': pitcher_stats,
                        'bench': our_bench if our_attack else opp_bench,
                        'bullpen': our_bullpen if not our_attack else opp_bullpen,
                        'outs': outs,
                        'runners': runners,
                        'score': score,
                        'chance_count': chance_count,
                        'max_chance': max_chance,
                        "player" : player
                    }
                    chance_count = chance_count + 1
                    pa_result = chance_result(context)
                    outs_inc, runners, runs, hit_streak = process_pa_result(pa_result, runners, hit_streak)
                    
                outs += outs_inc
                
                if hit_streak>3:
                    hit_streak = 0
                if runs > 0:
                    score_key = 'away' if atk_team == away else 'home'
                    score[score_key] += runs
                    sc = sc + runs
                    
                loc_score = {away: score['away'], home: score['home']}
                print(f"  아웃: {outs} 주자: {runners} 득점: {loc_score}")

                # 기록 업데이트
                hitter = atk_lineup[atk_idx]
                update_player_stats(
                    team_name if our_attack else opp_team,
                    [hitter],
                    def_pitcher
                )

                # 타순 인덱스 증가
                if our_attack:
                    our_idx = (our_idx + 1) % 9
                else:
                    opp_idx = (opp_idx + 1) % 9

                # 이닝 마무리
                if outs >= 3:
                    outs, runners = 0, []
                    sc = 0
                    half = 'bottom' if half == 'top' else 'top'
                    if half == 'top':
                        inning += 1

            # 경기 승패 업데이트
            winner = get_match_result_only(away, home, stad)
            loser  = home if winner == away else away
            # update_team_winloss(winner, 'win')
            # update_team_winloss(loser,  'loss')

    update_virtual_rankings()
    print("✅ 시즌 시뮬레이션 완료!")  
