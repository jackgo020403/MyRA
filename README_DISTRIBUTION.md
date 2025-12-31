# Research Assistant - 배포 가이드

## 🎉 앱 빌드하기

### 간단한 방법
1. `build_final.bat` 더블클릭
2. 2-3분 대기
3. `dist\ResearchAssistant.exe` 생성 완료!

### 수동 방법
```bash
pyinstaller build_app_lite.spec --clean
```

## 📦 배포하기

### 옵션 1: .exe만 공유 (권장)
- `dist\ResearchAssistant.exe` 파일만 보내면 됩니다
- 크기: ~100-150 MB
- 사용자가 첫 실행 시 API 키 입력

### 옵션 2: API 키 포함해서 공유
1. `.env` 파일 생성:
   ```
   ANTHROPIC_API_KEY=your_key_here
   SERPER_API_KEY=your_key_here
   ```
2. `.env` 파일을 `ResearchAssistant.exe`와 같은 폴더에 넣기
3. 폴더째로 압축해서 공유

## 👥 사용자 가이드

### 첫 실행
1. `ResearchAssistant.exe` 더블클릭
2. 창이 열리면 우측 상단 "⚙ Settings" 클릭
3. API 키 입력:
   - Anthropic: https://console.anthropic.com/
   - Serper: https://serper.dev/
4. OK 클릭

### 연구 시작하기
1. 하단 텍스트 박스에 연구 주제 입력
2. Send 클릭
3. AI와 대화하면서 연구 범위 설정:
   - AI가 제안하면 피드백 주기
   - "좋아요", "바꿔주세요", "건너뛰기" 등 자연스럽게 대화
4. 각 서브 질문 검토:
   - "approve" / "좋아요" = 승인
   - "skip" / "건너뛰기" = 제외
   - 수정 제안도 자유롭게
5. 모든 승인 후 연구 시작 (3-5분 소요)
6. 결과 Excel 파일 생성:
   - `outputs/` 폴더에 저장
   - 3개 탭: MEMO, SYNTHESIS, RAW DATA

## 🎯 주요 기능

### 완전한 대화형 인터페이스
- ChatGPT처럼 자연스러운 대화
- AI가 thought partner로 작동
- 무제한 피드백과 수정 가능

### 자동 연구 수행
- 50개 고품질 소스 검색
- 자동 증거 추출
- 질문별 분석 및 종합
- 경영진 요약 생성

### Excel 리포트
- **MEMO**: 핵심 내용 요약
- **SYNTHESIS**: 질문별 상세 분석 + 인용
- **RAW DATA**: 모든 증거와 출처 (클릭 가능한 링크)

## ⚙️ 시스템 요구사항

- **OS**: Windows 10 이상
- **RAM**: 4GB (8GB 권장)
- **디스크**: 500MB 여유 공간
- **인터넷**: API 호출 및 웹 검색용

## 🔧 문제 해결

### "API Keys Required" 오류
- Settings에서 API 키 입력했는지 확인
- 키가 유효한지 확인 (console.anthropic.com에서 테스트)

### 앱이 실행 안 됨
- Windows Defender가 차단했을 수 있음 → 허용 설정
- 관리자 권한으로 실행 시도

### Excel 파일을 찾을 수 없음
- `outputs/` 폴더 확인 (exe와 같은 위치)
- 채팅 창에 표시된 전체 경로 복사해서 탐색기에 붙여넣기

### 연구가 너무 오래 걸림
- 정상: 3-5분 소요 (50개 소스 검색 + 분석)
- 인터넷 연결 확인
- API 크레딧 잔액 확인

## 📝 사용 팁

### 좋은 연구 질문 예시
✅ "2022-2025년 한국 알바 플랫폼 시장 점유율 및 경쟁 구도"
✅ "2024년 AI safety 연구의 주요 트렌드 3가지"
✅ "SaaS 기업의 고객 유지 전략: Salesforce vs HubSpot 비교"

### 대화 팁
- **명확한 피드백**: "시장 점유율보다 비즈니스 모델에 집중해주세요"
- **자연스러운 표현**: "좋아요", "아니요", "바꿔주세요" 모두 작동
- **질문하기**: "이게 무슨 뜻인가요?", "더 자세히 설명해주세요"

### 질문 검토 시
- 너무 broad한 질문은 "더 구체적으로" 요청
- 너무 narrow한 질문은 "좀 더 넓게" 요청
- 불필요한 질문은 "skip" 또는 "건너뛰기"

## 🚀 고급 사용

### 개발 모드로 실행 (버그 수정용)
```bash
python gui_app_final.py
```
- 즉시 실행 (빌드 불필요)
- 에러 메시지 확인 가능
- 코드 수정 후 바로 테스트

### 재빌드 (수정 후)
```bash
# 빠른 재빌드 (캐시 사용)
pyinstaller build_app_lite.spec

# 완전 재빌드 (문제 발생 시)
pyinstaller build_app_lite.spec --clean
```

## 📄 라이선스 & 배포

- 자유롭게 공유 가능
- API 키는 사용자 책임
- API 비용은 사용자 부담

## 🆘 지원

문제 발생 시:
1. `outputs/` 폴더의 로그 확인
2. Settings에서 API 키 재입력
3. 앱 재시작

---

**이제 배포 준비 완료!** 🎉

`build_final.bat` 실행 → `dist\ResearchAssistant.exe` 공유하면 끝!
