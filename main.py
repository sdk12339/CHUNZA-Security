cat << 'EOF' > main.py
import asyncio
import bot1
import bot2
import os

async def start_system():
    os.system('clear')
    print("====================================")
    print("   🛡️ CHUNZA 통합 시스템 v2.8")
    print("====================================")
    print(" [1] 보안 봇(bot1)만 가동")
    print(" [2] 춘자 봇(bot2)만 가동")
    print(" [3] 두 봇 모두 가동 (각각 설정)")
    print(" [0] 종료")
    print("====================================")
    
    choice = input("▶️ 번호 선택: ").strip()
    if choice == '0': return

    tasks = []

    # [1] 보안 봇 설정 (1번 또는 3번 선택 시)
    if choice in ['1', '3']:
        print("\n--- [보안 봇(bot1) 설정] ---")
        t1 = input("▶️ 보안 봇 토큰: ").strip()
        g1 = input("▶️ 보안 봇 서버 ID: ").strip()
        # bot1.py 내부에서 서버 ID를 처리하는 로직이 있다면 g1을 사용하도록 설정
        tasks.append(bot1.bot.start(t1))
        
    # [2] 춘자 봇 설정 (2번 또는 3번 선택 시)
    if choice in ['2', '3']:
        print("\n--- [춘자 봇(bot2) 설정] ---")
        t2 = input("▶️ 춘자 봇 토큰: ").strip()
        g2 = input("▶️ 춘자 봇 서버 ID: ").strip()
        # bot2.py 내부에서 서버 ID를 처리하는 로직이 있다면 g2를 사용하도록 설정
        tasks.append(bot2.bot.start(t2))

    if tasks:
        print("\n🚀 입력하신 설정으로 각 봇을 연결합니다...")
        # asyncio.gather를 통해 에러 없이 병렬 실행
        try:
            await asyncio.gather(*tasks)
        except Exception as e:
            print(f"\n❌ 가동 중 오류 발생: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(start_system())
    except KeyboardInterrupt:
        print("\n👋 시스템을 안전하게 종료합니다.")
EOF
