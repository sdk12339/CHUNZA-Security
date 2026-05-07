# 🛡️ CHUNZA Security & Management System (v1.5.0)

![CHUNZA Banner](https://img.shields.io/badge/CHUNZA-SECURITY-cyan?style=for-the-badge&logo=discord)
![Version](https://img.shields.io/badge/Version-1.5.0-yellow?style=for-the-badge)

**CHUNZA**는 디스코드 서버의 보안과 관리를 통합적으로 수행하는 강력한 올인원 툴입니다. 
Termux 및 Replit 환경에 최적화되어 있으며, 실시간 모니터링과 다양한 관리 명령어를 제공합니다.

---

## 🚀 주요 기능 (Core Features)

### 1. 강력한 보안 (Security)
* **관리자 감시:** 서버 내 관리자 권한 변동 및 위험한 역할 생성을 실시간으로 터미널에 보고합니다.
* **스팸 및 링크 차단:** 일반 유저의 도배와 허용되지 않은 링크 전송을 즉시 삭제하고 경고합니다.

### 2. 효율적인 관리 (Management)
* **투표 시스템:** 익명 투표 기능을 통해 서버 내 의사결정을 돕습니다.
* **메시지 청소:** 대량의 메시지를 한 번에 삭제하여 채널을 정리합니다.
* **채널 제어:** 명령어를 통해 채널 잠금, 해제, 생성 및 삭제를 즉시 수행합니다.

### 3. 데이터 보존 (Data Backup)
* **자동 백업:** `server_data.json` 파일을 통해 관리자 명단과 설정값을 안전하게 보관합니다.

---

## 🛠️ 명령어 리스트 (Commands)

| 구분 | 명령어 | 설명 |
| :--- | :--- | :--- |
| **일반** | `!문의`, `!현황`, `!투표`, `!결과` | 건의 전달, 서버 인원 확인, 익명 투표 |
| **관리** | `!청소`, `!추방`, `!차단`, `!잠금`, `!해제` | 서버 보안 및 유저 관리 |
| **설정** | `!생성`, `!삭제`, `!백업`, `!복구` | 서버 환경 및 데이터 관리 |
| **마스터**| `!권한부여`, `!권한해제` | 관리자 명단 등록 및 삭제 |

---

## 👤 Developer & Contact

문의 사항이나 업데이트 관련 정보는 아래 채널을 통해 확인하세요.

* **Developer:** h_wang07
* **Instagram:** [@h_wang07](https://www.instagram.com/h_wang07?igsh=MTB3MjJiMXFxdnFraQ%3D%3D&utm_source=qr)
* **Link:** https://www.instagram.com/h_wang07?igsh=MTB3MjJiMXFxdnFraQ%3D%3D&utm_source=qr

---

## ⚠️ Requirements
* `discord.py`
* `flask`
* `python 3.10+`

Copyright 2026. **CHUNZA** all rights reserved.
