import threading
import bot1
import bot2
import os

def start_system():
    # 터미널 화면을 깨끗하게 정리합니다.
    os.system('clear' if os.name == 'posix' else 'cls')
    
    print("==========================================")
    print("   🛡️ MARONG-CITY 통합 관리 시스템 v2.0")
    print("==========================================\n")
    
    # 1. 사용자로부터 직접 정보를 입력받음 (여기서 입력한 값이 봇으로 전달됨)
    t1_token = input("▶️ 보안 봇(bot1) 토큰 입력: ").strip()
    t2_token = input("▶️ 춘자 봇(bot2) 토큰 입력: ").strip()
    guild_id = input("▶️ 관리할 서버(Guild) ID 입력: ").strip()

    if not t1_token or not t2_token:
        print("\n❌ 오류: 토큰이 입력되지 않았습니다. 다시 실행해 주세요.")
        return

    # 2. 멀티스레딩을 사용하여 두 봇을 동시에 가동
    # 각 파일의 run_bot 함수에 사용자가 입력한 토큰을 인자로 넘겨줍니다.
    thread1 = threading.Thread(target=bot1.run_bot, args=(t1_token, guild_id))
    thread2 = threading.Thread(target=bot2.run_bot, args=(t2_token, guild_id))

    print("\n🛠️ 입력하신 정보로 봇 연결을 시도합니다...")
    
    thread1.start()
    thread2.start()

    print("✅ 가동 명령이 전달되었습니다. (에러 발생 시 아래에 표시됨)\n")

if __name__ == "__main__":
    start_system()
