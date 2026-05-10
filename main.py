import threading
import bot1
import bot2
import os

# [1] 시스템 시작 함수
def start_system():
    # 터미널 화면 청소
    os.system('clear' if os.name == 'posix' else 'cls')
    
    print("====================================")
    print("   🛡️ CHUNZA 통합 제어 시스템 v1.8.0")
    print("====================================\n")
    
    # 24시간 유지를 위한 웹 서버는 필요 시 여기서 실행 (선택사항)
    
    # 사용자로부터 직접 입력 받기
    t1_token = input("▶️ 보안 봇(bot1) 토큰 입력: ").strip()
    t2_token = input("▶️ 춘자 봇(bot2) 토큰 입력: ").strip()
    guild_id = input("▶️ 대상 서버 ID 입력: ").strip()

    if not t1_token or not t2_token:
        print("\n❌ 오류: 토큰이 입력되지 않았습니다.")
        return

    # 각 봇을 별도 스레드에서 가동
    try:
        thread1 = threading.Thread(target=bot1.run_bot, args=(t1_token, guild_id))
        thread2 = threading.Thread(target=bot2.run_bot, args=(t2_token, guild_id))

        print("\n🛠️ 봇 연결 시도 중... 입력하신 토큰으로 로그인을 시작합니다.")
        thread1.start()
        thread2.start()
        
        print("✅ 가동 명령 전달 완료.")
    except Exception as e:
        print(f"❌ 가동 중 오류 발생: {e}")

# [2] 메인 진입점 (기존의 모든 bot.run 코드는 여기서 삭제됨)
if __name__ == "__main__":
    start_system()
