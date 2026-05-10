import threading
import bot1
import bot2
import os

def start_system():
    # 터미널 화면 정리
    os.system('clear' if os.name == 'posix' else 'cls')
    
    print("====================================")
    print("   🛡️ CHUNZA 통합 제어 시스템 v1.8.0")
    print("====================================\n")
    
    # [1] 사용자로부터 직접 토큰과 ID 입력 받기
    # .strip()을 넣어 혹시 모를 공백(스페이스)을 제거합니다.
    t1_token = input("▶️ 보안 봇(bot1) 토큰 입력: ").strip()
    t2_token = input("▶️ 춘자 봇(bot2) 토큰 입력: ").strip()
    guild_id = input("▶️ 대상 서버 ID 입력: ").strip()

    if not t1_token or not t2_token:
        print("\n❌ 오류: 토큰이 입력되지 않았습니다.")
        return

    # [2] 스레드를 사용하여 두 봇을 병렬 실행
    # 각 파일의 run_bot 함수에 입력받은 값을 전달합니다.
    try:
        thread1 = threading.Thread(target=bot1.run_bot, args=(t1_token, guild_id))
        thread2 = threading.Thread(target=bot2.run_bot, args=(t2_token, guild_id))

        print("\n🛠️ 봇 연결을 시도합니다...")
        thread1.start()
        thread2.start()
        
        print("✅ 가동 명령 전달 완료 (에러 발생 시 아래에 표시됨)")
    except Exception as e:
        print(f"❌ 시스템 시작 오류: {e}")

if __name__ == "__main__":
    start_system()
