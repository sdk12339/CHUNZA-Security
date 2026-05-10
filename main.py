cat << 'EOF' > main.py
import threading
import bot1
import bot2
import os

def start_system():
    os.system('clear')
    print("====================================")
    print("   🛡️ CHUNZA 통합 시스템 v2.0")
    print("====================================\n")
    
    t1 = input("▶️ 보안 봇(bot1) 토큰: ").strip()
    t2 = input("▶️ 춘자 봇(bot2) 토큰: ").strip()
    gid = input("▶️ 서버 ID: ").strip()

    if not t1 or not t2:
        print("❌ 토큰을 입력하지 않았습니다.")
        return

    # 두 봇을 병렬 실행 (각 파일에 run_bot 함수가 있어야 함)
    threading.Thread(target=bot1.run_bot, args=(t1, gid)).start()
    threading.Thread(target=bot2.run_bot, args=(t2, gid)).start()
    
    print("\n🚀 봇들이 연결 중입니다... 터미널 로그를 확인하세요.")

if __name__ == "__main__":
    start_system()
EOF
