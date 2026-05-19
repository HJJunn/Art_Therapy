# HTP 심리검사 챗봇 서비스 (챗쪽이)

HTP (House-Tree-Person) 투사 그림 검사를 기반으로 한 AI 심리 분석 챗봇 시스템입니다.

## 📋 목차
- [프로젝트 구조](#프로젝트-구조)
- [기술 스택](#기술-스택)
- [Runpod 배포 가이드](#runpod-배포-가이드)
- [로컬 개발 환경 설정](#로컬-개발-환경-설정)
- [주요 기능](#주요-기능)

---

## 🗂 프로젝트 구조

```
web_all/
├── web_back-main/          # FastAPI 백엔드 서버
│   ├── multi_main.py        # 메인 API 엔드포인트
│   ├── model.py             # Qwen 모델 (helena29/Qwen2.5_LoRA_for_HTP)
│   ├── caption.py           # 이미지 캡션 생성 (Florence-2-large)
│   ├── rag_engine.py        # RAG 검색 엔진
│   ├── embeddings.py        # 벡터 DB
│   ├── requirements.txt     # Python 의존성
│   ├── .env                 # 환경 변수 (OpenAI API Key)
│   └── data/                # HTP 관련 논문/자료
└── web_front-main/          # React 프론트엔드
    ├── src/
    │   ├── HTPChatbot.jsx   # 메인 챗봇 컴포넌트
    │   └── ...
    ├── package.json
    └── .env                 # 환경 변수 (API URL)
```

---

## 🛠 기술 스택

### Backend
- **Framework**: FastAPI
- **AI Models**: 
  - Qwen2.5 LoRA (HTP 해석)
  - Florence-2-large (이미지 캡션)
  - GPT-4o (최종 종합 해석)
  - GPT-4o-mini (번역)
- **Vector DB**: ChromaDB
- **Language**: Python 3.12

### Frontend
- **Framework**: React
- **Styling**: Tailwind CSS
- **Language**: JavaScript

---

## 🚀 Runpod 배포 가이드

### 1. 백엔드 배포 (web_back-main)

#### 1.1 초기 설정
```bash
# 레포지토리 클론
git clone https://github.com/Art-Therapy-Chat/web_all.git
cd web_all/web_back-main

# 환경 변수 설정
nano .env
```

**`.env` 파일 내용:**
```
OPENAI_API_KEY=your_openai_api_key_here
```

#### 1.2 의존성 설치
```bash
pip install -r requirements.txt
```

#### 1.3 포트 충돌 해결 (필요 시)
```bash
# 8888 포트 사용 중인 프로세스 확인
lsof -i :8888

# 프로세스 종료
kill -9 <PID>
```

#### 1.4 서버 실행
```bash
uvicorn multi_main:app --host 0.0.0.0 --port 8888
```

**백엔드 URL**: `https://[POD_ID]-[PORT_NUM].proxy.runpod.net` (Runpod에서 서버를 띄울시=> 다른 환경에서 서버 띄울시 변경필수)

---

### 2. 프론트엔드 배포 (web_front-main)

#### 2.1 Node.js 설치 (필요 시)
```bash
# Runpod 환경에서 Node.js 설치
curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
apt-get install -y nodejs
```

#### 2.2 환경 변수 설정
```bash
cd ../web_front-main
nano .env
```

**`.env` 파일 내용:**
```
REACT_APP_API_URL=https://[POD_ID]-[PORT_NUM].proxy.runpod.net (백엔드 URL)
```

> ⚠️ **중요**: Pod이 재시작되거나 변경될 때마다 `[POD_ID]`를 업데이트해야 합니다.

#### 2.3 의존성 설치 및 실행
```bash
npm install
npm start
```

**프론트엔드 URL**: `http://localhost:3000`

---

### 3. Pod 관리

#### Pod 중지
```bash
runpodctl stop pod [POD_ID]
```

#### Pod 재시작 시 체크리스트
- [ ] 백엔드 `.env` 파일 확인
- [ ] 프론트엔드 `.env`의 `REACT_APP_API_URL` 업데이트
- [ ] 포트 충돌 확인 (`lsof -i :8888`)
- [ ] 서버 재실행

---

## 💻 로컬 개발 환경 설정

### 백엔드
```bash
cd web_back-main

# 가상환경 생성 (선택사항)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# .env 파일 생성
echo "OPENAI_API_KEY=your_key_here" > .env

# 서버 실행
uvicorn multi_main:app --reload --port 8000
```

### 프론트엔드
```bash
cd web_front-main

# .env 파일 생성
echo "REACT_APP_API_URL=http://localhost:8000" > .env

# 의존성 설치 및 실행
npm install
npm start
```

로컬 접속: http://localhost:3000

---

## ✨ 주요 기능

### 1. 그림 분석 파이프라인
1. **이미지 캡션 생성** (Florence-2-large)
   - 집, 나무, 사람 그림 특징 추출
   
2. **RAG 기반 참고문헌 검색**
   - HTP 관련 논문 및 자료 검색
   - 멀티쿼리 재작성 (GPT-4o)
   
3. **개별 해석 생성** (Qwen2.5 LoRA)
   - 각 그림별 심리 분석
   - 참고문헌 기반 해석
   
4. **번역** (GPT-4o-mini)
   - 영어 해석 → 한국어 번역

### 2. 대화형 추가 질문 (5회)
- 부모(관찰자) 시점 질문
- 고정형 한국어 질문 순차 제공
- 아이의 그림 과정 관찰 내용 수집

### 3. 최종 종합 해석 (GPT-4o)
- 3가지 그림 통합 분석
- 대화 내용 반영
- 사용자 정보(이름, 나이, 성별) 고려

---

## 📝 API 엔드포인트

| 엔드포인트 | 메서드 | 설명 |
|-----------|--------|------|
| `/caption` | POST | 이미지 캡션 생성 |
| `/rag` | POST | RAG 문서 검색 |
| `/interpret_single` | POST | 개별 그림 해석 |
| `/translate` | POST | 영어→한국어 번역 |
| `/questions` | POST | 추가 질문 생성 (고정 5개) |
| `/interpret_final` | POST | 최종 종합 해석 |

---

## 🔧 트러블슈팅

### 포트 충돌 에러
```
[Errno 98] error while attempting to bind on address ('0.0.0.0', 8888): address already in use
```

**해결책:**
```bash
lsof -i :8888
kill -9 <PID>
```

### CORS 에러
백엔드 `multi_main.py`에서 CORS 설정 확인:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 모델 로딩 실패
- GPU 메모리 확인
- Hugging Face 모델 다운로드 상태 확인
- CUDA 사용 가능 여부 확인

---

## 📄 라이센스

이 프로젝트는 교육 목적으로 개발되었습니다.

---

## 👥 개발팀

Art-Therapy-Chat

---

## 📞 문의

Issue를 통해 문의해주세요: [GitHub Issues](https://github.com/Art-Therapy-Chat/web_all/issues)
