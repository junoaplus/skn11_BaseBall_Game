# llm/eeve_client.py

from ollama import Client

def get_decision_from_llm(prompt: str) -> str:
    try:
        client = Client(host='http://localhost:11434')  # Ollama 서버 기본 포트
        response = client.chat(model='llama3.2', messages=[
            {"role": "system", "content": "당신은 야구 작전 코치입니다."},
            {"role": "user", "content": prompt}
        ])
        return response['message']['content'].strip()
    except Exception as e:
        print("🛑 LLM 실행 실패:", e)
        return "강공을 선택합니다. 기본 판단입니다."
