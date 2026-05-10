import asyncio
import bot1
import bot2
import os

async def start_system():
    os.system('clear')
    print("====================================")
    print("   🛡️ CHUNZA 통합 시스템 v3.1")
    print("====================================")
    print(" [1] 보안 봇(bot1)만 가동")
    print(" [2] 춘자 봇(bot2)만 가동")
    print(" [3] 두 봇 모두 가동")
    print(" [0] 종료")
    print("====================================")
    
    choice = input("▶️ 번호 선택: ").strip()
    if choice == '0': return

    tasks = []
    
    # 보안 봇 설정
    if choice in ['1', '3']:
        print("\n--- [보안 봇 설정] ---")
        t1 = input("▶️ 토큰: ").strip()
        g1 = input("▶️ 서버 ID: ").strip()
        # 함수 자체를 넘기는 게 아니라 호출한 결과(코루틴)를 넘깁니다.
        tasks.append(bot1.run_bot(t1, g1))
        
    # 춘자 봇 설정
    if choice in ['2', '3']:
        print("\n--- [춘자 봇 설정] ---")
        t2 = input("▶️ 토큰: ").strip()
        g2 = input("▶️ 서버 ID: ").strip()
        tasks.append(bot2.run_bot(t2, g2))

    if tasks:
        print("\n🚀 봇 연결 중... (충돌 방지 모드)")
        # gather를 통해 여러 봇을 안전하게 병렬 실행합니다.
        await asyncio.gather(*tasks)

if __name__ == "__main__":
    try:
        asyncio.run(start_system())
    except KeyboardInterrupt:
        print("\n👋 프로그램을 종료합니다.")
