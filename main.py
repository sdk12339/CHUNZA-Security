import threading
import bot1
import bot2
import os

def start_system():
    os.system('clear' if os.name == 'posix' else 'cls')
    
    print("====================================")
    print("   🛡️ CHUNZA 통합 시스템 v2.5")
    print("====================================")
    print(" [1] 보안 봇(bot1)만 가동")
    print(" [2] 춘자 봇(bot2)만 가동")
    print(" [3] 두 봇 모두 가동")
    print(" [0] 종료")
    print("====================================")
    
    choice = input("▶️ 실행할 번호를 선택하세요: ").strip()

    if choice == '0':
        print("시스템을 종료합니다.")
        return

    # 공통 서버 ID 입력
    guild_id = input("\n▶️ 대상 서버 ID 입력: ").strip()

    if choice == '1':
        t1 = input("▶️ 보안 봇(bot1) 토큰 입력: ").strip()
        threading.Thread(target=bot1.run_bot, args=(t1, guild_id)).start()
        print("\n🚀 보안 봇 가동 중...")

    elif choice == '2':
        t2 = input("▶️ 춘자 봇(bot2) 토큰 입력: ").strip()
        threading.Thread(target=bot2.run_bot, args=(t2, guild_id)).start()
        print("\n🚀 춘자 봇 가동 중...")

    elif choice == '3':
        t1 = input("▶️ 보안 봇(bot1) 토큰 입력: ").strip()
        t2 = input("▶️ 춘자 봇(bot2) 토큰 입력: ").strip()
        threading.Thread(target=bot1.run_bot, args=(t1, guild_id)).start()
        threading.Thread(target=bot2.run_bot, args=(t2, guild_id)).start()
        print("\n🚀 모든 봇 가동 중...")

    else:
        print("❌ 잘못된 번호입니다. 다시 실행해 주세요.")

if __name__ == "__main__":
    start_system()
