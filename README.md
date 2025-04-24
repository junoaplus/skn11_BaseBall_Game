# 📖 KBO 야구 시뮬레이터 프로젝트

## 프로젝트 개요
이 프로젝트는 KBO 2024 시즌 실제 데이터를 바탕으로, 감독이 팀을 선택하고 직접 라인업을 구성하여 9이닝 게임을 시뮬레이트하는 콘솔 기반 시뮬레이터입니다.  
LLM(EEVE-Korean-10.8B)을 활용해 PA 결과를 생성하고, ‘찬스’ 상황에서는 감독이 직접 판단을 내려 승부를 뒤집을 수 있는 인터랙티브한 기능을 제공합니다.


---

## 📂 디렉터리 구조

    .
    ├── data/                     # 원본 CSV 데이터  
    │   ├── players_2024.csv  
    │   ├── players_P_2024.csv  
    │   └── schedule_2024.csv  
    ├── db/                       # DB 스키마 및 초기화 스크립트  
    │   ├── batter.py  
    │   ├── picher.py  
    │   └── schedule.py  
    │   └── aql  
    ├── game/                     # 게임 로직 모듈  
    │   ├── manager.py            # 팀/라인업 선택  
    │   ├── engine.py             # 시뮬레이션 엔진(play_season)  
    │   ├── database.py           # DB 조회/업데이트 함수  
    │   └── decision.py           # PA 결과 처리(process_pa_result)  
    ├── llm/                      # LLM 통합 모듈  
    │   ├── eeve_client.py        # Ollama EEVE 클라이언트 래퍼  
    │   └── game_runner.py        # LLM 기반 PA·찬스·승자 판단 함수  
    ├── main.py                   # 진입점: select_team → select_lineup →play_season  
    ├── README.md                 # 이 문서  

---

## 🏗️ 개발 진행 일정

- **4월 21일 (월)**  
  - 데이터 크롤링 및 CSV 파일 수집  
  - data/ 폴더에 초기 데이터 배치  

- **4월 22일 (화)**  
  - MySQL 스키마 설계 및 db/ 스크립트 작성  
  - CSV → DB 삽입 로직 검증  

- **4월 23일 (수)**  
  - game/manager.py에서 감독 입력 및 라인업 선택 기능 구현  
  - game/engine.py 기본 시뮬레이션 루프 작성 (이닝, 아웃, 점수 집계)  

- **4월 24일 (목)**  
  - LLM 연동: llm/game_runner.py에 EEVE 채팅 프롬프트 작성  
  - 찬스 상황 판단(is_chance_eligible) 및 인터랙티브 ‘찬스’ 처리 기능 완성  
  - 전체 시뮬레이션 통합 테스트 및 최종 디버깅

---

## 🚀 주요 기능 상세

1. **팀 선택 & 라인업 구성**  
    - 기존 감독 아이디로 저장된 팀 불러오기  
    - 신규 감독은 10개 팀 중 선택 → user_team 테이블에 저장  
    - WAR 순으로 정렬된 타자·투수 후보 리스트에서 감독이 직접 선택

2. **시뮬레이션 엔진 (play_season)**  
    - 9이닝, 주자·아웃·점수 상태를 단계별로 진행  
    - ask_pa_result → LLM을 사용해 PA 결과(안타, 아웃, 찬스 등) 생성  
    - process_pa_result → 결과에 따라 주자 이동 및 득점 계산  

3. **찬스 인터랙션**  
    - is_chance_eligible 로 찬스 가능 여부 판단  
    - ‘찬스’ 발생 시 콘솔에서 감독 판단 입력  
    - chance_result 로 감독 판단과 스탯을 기반으로 최종 PA 결과 생성  

4. **1~9회 진행**
    - 1~9회까지 경기를 진행 후 종료 된다.

---

## 🙋‍♂️ 확장 아이디어

- UI/UX 개선: Streamlit 또는 웹 프레임워크로 시각화  
- 추가 모드: 연습 경기, 토너먼트 모드  
- 다양한 LLM 모델 지원: GPT-4, Llama 등  
- 통계 리포트: 시즌 종료 후 주요 지표 자동 생성  


---

 ## 한줄 회고

 - EEVE가 promt를 길게 주면 이해를 못하고 야구에 대해서 이해를 하지 못해서 너무 힘들었다. 그래서 게임 엔진을 만들서 넘겨줬는데도 점수를 너무 크게 내서 너무 힘들었습니다. 하지만 프롬프트를 많이 손을 보면서 차근 차근 고쳐 나갔습니다.
