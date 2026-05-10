import asyncio
import bot1
import bot2
import os

async def start_system():
    os.system('clear')
    print("====================================")
    print("   🛡️ CHUNZA 통합 시스템 v3.2")
    print("====================================")
    print(" [1] 보안 봇(bot1)만 가동")
    print(" [2] 춘자 봇(bot2)만 가동")
    print(" [3] 두 봇 모두 가동")
    print(" [0] 종료")
    print("====================================")
    
    choice = input("▶️ 번호 선택: ").strip()
    if choice == '0': return

    tasks = []
    
    if choice in ['1', '3']:
        print("\n--- [보안 봇 설정] ---")
        t1 = input("▶️ 토큰: ").strip()
        g1 = input("▶️ 서버 ID: ").strip()
        # 함수를 호출하여 코루틴 객체를 tasks에 넣습니다.
        tasks.append(bot1.run_bot(t1, g1))
        
    if choice in ['2', '3']:
        print("\n--- [춘자 봇 설정] ---")
        t2 = input("▶️ 토큰: ").strip()
        g2 = input("▶️ 서버 ID: ").strip()
        tasks.append(bot2.run_bot(t2, g2))

    if tasks:
        print("\n🚀 봇 연결 시도 중... (충돌 방지 모드 가동)")
        # gather를 통해 모든 코루틴을 병렬로 안전하게 실행합니다.
        await asyncio.gather(*tasks)

if __name__ == "__main__":
    try:
        # 시스템 전체의 유일한 이벤트 루프 시작점입니다.
        asyncio.run(start_system())
    except KeyboardInterrupt:
        print("\n👋 종료합니다.")
