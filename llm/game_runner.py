import pandas as pd
import pymysql
import json
import re
from ollama import chat
import random
from json import JSONDecodeError
from dotenv import load_dotenv
import openai

# 환경 변수에서 API 키 로드 후 OpenAI client 생성
load_dotenv()
client = openai.OpenAI()


def get_team_stats(team):
    """
    2024 시즌 해당 팀의 실제 타자·투수 스탯을
    hitters, pitchers 두 개의 DataFrame으로 반환합니다.
    """
    conn = pymysql.connect(
        host='localhost', user='root', password='030617',
        db='kbo_simulator', charset='utf8'
    )
    hitters = pd.read_sql(
        """
        SELECT Rank, Name, Team, Year,
               WAR, PA, AVG, OBP, SLG, OPS,
               WPA, spAVG, spOBP, spSLG, spOPS
        FROM hitters
        WHERE Team = %s
        ORDER BY WAR DESC
        """, conn, params=(team,)
    )
    pitchers = pd.read_sql(
        """
        SELECT Rank, Name, Team,
               WAR, G, GS, IP, ERA, WHIP,
               SO, BB, H, HR, WP, BK, SB
        FROM pitchers
        WHERE Team = %s
        ORDER BY WAR DESC
        """, conn, params=(team,)
    )
    conn.close()
    return hitters, pitchers


def is_chance_eligible(context):
    """
    찬스(Clutch) 상황이 가능한지 여부를 판단합니다.
    """
    inning = context.get('inning', 0)
    runners = context.get('runners', [])
    our_attack = context.get('our_attack', False)
    score = context.get('score', {'home': 0, 'away': 0})
    home, away = score.get('home', 0), score.get('away', 0)
    total_score = home + away
    # 이닝별 찬스 사용 횟수 제한 로직은 외부에서 chance_count로 관리

    if not our_attack:
        return False
    if len(runners) < 2:
        return False
    if abs(home - away) > 4:
        return False
    return True


def ask_pa_result(context, sc, hit_streak):
    """
    context를 바탕으로 LLM에게 매번 독립 샘플링하고
    같은 결과가 연속되지 않도록 지시하여 PA 결과를 결정합니다.
    """
    
    eligible = is_chance_eligible(context)
    score = context.get('score', {'home': 0, 'away': 0})
    home, away = score['home'], score['away']
    total_score = home + away
    inning = context.get('inning', 0)
    chance_count = context.get('chance_count', 0)

    base_outcomes = [
        'strikeout', 'groundout', 'flyout', 'pop out',
        'single', 'double', 'triple', 'home run', 'base on balls'
    ]
    possible_outcomes = base_outcomes + (['chance'] if eligible else [])

    if eligible:
        weights = [0.025]*4 + [0.02]*5 + [0.80]
    else:
        weights = [0.18]*4 + [0.02]*5
        
    if 4 < sc:
        weights = [0.18]*4 + [0.0]*5
    elif hit_streak>4:
        weights = [0.18]*4 + [0.0]*5
    system_prompt = f"""
너는 KBO 시뮬레이터 전용 LLM이다. 아래 규칙을 **엄격히** 지켜라.


1. 가능한 출력값(반드시 1개만):
   {', '.join(possible_outcomes)}

2. 점수 제약:
   - 합산 점수: {total_score}
   - 이닝: {inning}, 찬스 사용 횟수: {chance_count}

3. 가중치(확률 분포):
   - 아웃: {sum(weights[:4])*100:.0f}%  
   - 안타: {sum(weights[4:9])*100:.0f}%  
   - 찬스({eligible}): {weights[-1]*100:.0f}%

4. 독립 시행:
   - **이전 PA 결과와 전혀 상관없이**, 매번 완전히 독립적으로 샘플링하라.

5. 연속 결과 제한:
   - **같은 PA 결과가 2회 연속으로 나오지 않도록** 내부에서 주의하라.

6. 출력 형식:
   - 위 1번 목록 중 하나만, 다른 단어·공백·설명 없이 응답하라.
"""

    user_content = json.dumps(context, ensure_ascii=False, default=str)
    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_content}
        ]
    )
    return res.choices[0].message.content.strip(), hit_streak



def chance_result(context):

    base_outcomes = [
        'strikeout', 'groundout', 'flyout', 'pop out',
        'single', 'double', 'triple', 'home run', 'base on balls'
    ]
    
    system_prompt = """
        1. 가능한 출력값(반드시 1개만):
        - {base_outcomes}
        
        2. 출력 형식:
        - 첫 줄에 영어 결과 하나만 {base_outcomes} 목록 중 하나만
         예시
        - 'single'
        - 'strikeout'
        - 'groundout'
        - 'flyout'
        -  'pop out'
        - 'double'
        - 'triple'
        - 'home run'
        - 'base on balls'
        무조건 이 9개의 형식으로만 답을 해야돼 
        어떤 한국 말을 하든 결과는 무조건 영어로 해줘야돼 위의 9개 내에서

        
        3. 결과
        - 결과는 감독의 지시를 수행하는거야 감독의 지시를 수행했을때 어떤 결과가 나올지 예측하는거지 너 마음대로 이러한 선수니까 이런 타격을 이런 결과가 나올거다 라고 생각하는게 아니라 
        - 반드시 위의 예시 처럼 처음에 결과를 보내줘야돼 반드시, 결과는 한여야만 하고 
        - 감독이 요청한 대로만 판단(player) 답을 주면 안돼 선수의 전력 비교와 비교를 통해 갑독이 요청한 행동을 했을때 데이터 기반 어떤 결과가 나올지를 답해주는거야 
        - homerun(홈런)은 너무 자주 나오면 안돼 5번중 1번의 확률로 나오면 좋겠어
        4. 너에 대한 인식
        "너는 야구를 아주 잘 알고 있는 시뮬레이션 LLM이야. "
        "context 안의 선수 스탯과 user 판단(player) 정보를 바탕으로 "
        "결과를 'strikeout','groundout','flyout','pop out',"
        "'single','double','triple','home run','base on balls' 중 "
        "하나만 정확히 반환해. "
        "유저가 원하는 답만 전달해줘서는 안 돼. "
        "그 상황과 그 선수의 실제 스텟을 비교해서 결과를 반영해줘."
"""
    user_content = json.dumps(context, ensure_ascii=False, default=str)
    

    response = chat(
        model="EEVE-Korean-10.8B",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_content}
        ],
        stream=False 
    )

    return response["message"]["content"].strip()

def get_match_result_only(t1, t2, stad):
    """
    두 팀 경기 결과 중 승자만 반환합니다.
    """
    system_prompt = "승자만 알려줘."
    user_content = f"{t1} vs {t2} @ {stad}"
    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]
    )
    content = res.choices[0].message.content
    for t in (t1, t2):
        if t in content and '승' in content:
            return t
    return None


def ask_roster(team, hitters_df, pitchers_df, max_retries=3):
    """
    LLM에게 JSON 포맷의 로스터를 요청합니다.
    """
    batters = hitters_df['Name'].tolist()
    pitchers = pitchers_df['Name'].tolist()

    system_msg = {"role": "system", "content": "오직 JSON 포맷만, 다른 말 없이 출력하세요."}
    user_msg = {"role": "user",
        "content": (
            f"{team} 팀의 로스터를 JSON으로 만들어주세요.\n"
            "- lineup: 타자 9명 리스트\n"
            "- bench: 나머지 타자 리스트\n"
            "- starting: 선발 투수 한 명\n"
            "- bullpen: 나머지 투수 리스트\n"
            f"타자 후보: {batters}\n투수 후보: {pitchers}"
        )
    }

    for attempt in range(max_retries):
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[system_msg, user_msg]
        )
        content = response.choices[0].message.content.strip()

        try:
            data = json.loads(content)
        except JSONDecodeError:
            m = re.search(r'(\{.*\})', content, re.DOTALL)
            if m:
                try:
                    data = json.loads(m.group(1))
                except JSONDecodeError:
                    data = None
            else:
                data = None

        if isinstance(data, dict) and all(k in data for k in ('lineup','bench','starting','bullpen')):
            return data

    # 폴백 로스터
    return {
        'lineup': batters[:9],
        'bench': batters[9:],
        'starting': random.choice(pitchers),
        'bullpen': [p for p in pitchers if p != random.choice(pitchers)]
    }
