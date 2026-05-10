import threading
import bot1
import bot2
from flask import Flask
from threading import Thread

# [1] 24시간 유지를 위한 공통 웹 서버
app = Flask('')
@app.route('/')
def home(): return "마롱특별시 관리 시스템 가동 중"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()

# [2] 두 봇 동시 가동
if __name__ == "__main__":
    print("🛠️ 시스템 통합 가동을 시작합니다...")
    keep_alive()  # 웹 서버 실행
    
    # 각 파일의 run_bot 함수를 스레드로 실행
    t1 = threading.Thread(target=bot1.run_bot)
    t2 = threading.Thread(target=bot2.run_bot)
    
    t1.start()
    print("✅ bot1.py 연결 완료")
    
    t2.start()
    print("✅ bot2.py 연결 완료")
