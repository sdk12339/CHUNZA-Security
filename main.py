import asyncio
import bot1
import bot2
import os

async def run_system():
    os.system('clear' if os.name == 'posix' else 'cls')
    
    print("====================================")
    print("   🛡️ CHUNZA 통합 시스템 v2.6")
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

    guild_id = input("\n▶️ 대상 서버 ID 입력: ").strip()

    # [1] 보안 봇 설정
    if choice in ['1', '3']:
        t1 = input("▶️ 보안 봇(bot1) 토큰 입력: ").strip()
    
    # [2] 춘자 봇 설정
    if choice in ['2', '3']:
        t2 = input("▶️ 춘자 봇(bot2) 토큰 입력: ").strip()

    print("\n🛠️ 봇 연결 시도 중... (비동기 모드)")

    # 봇 가동 로직
    tasks = []
    if choice == '1':
        tasks.append(bot1.bot.start(t1))
    elif choice == '2':
        tasks.append(bot2.bot.start(t2))
    elif choice == '3':
        tasks.append(bot1.bot.start(t1))
        tasks.append(bot2.bot.start(t2))

    if tasks:
        # 두 봇을 충돌 없이 동시에 실행합니다.
        await asyncio.gather(*tasks)

if __name__ == "__main__":
    try:
        asyncio.run(run_system())
    except KeyboardInterrupt:
        print("\n👋 시스템을 종료합니다.")
    except Exception as e:
        print(f"\n❌ 치명적 오류 발생: {e}")
