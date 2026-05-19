# 🎨 Art Therapy Chatbot


> HTP(House-Tree-Person) 그림 검사 기반의 심리 해석을 위해  
> 이미지 캡셔닝, 컴퓨터 비전, RAG, LLM 파인튜닝을 결합한  
> AI 기반 심리 상담 챗봇 프로젝트입니다.
> ####  My Role
> RAG 파트 👉 https://github.com/HJJunn/Art_Therapy_Chat_bot
---

# 🚀 Overview

본 프로젝트는 사용자가 업로드한 HTP 그림 이미지를 분석하여  
그림 속 객체를 탐지하고, 이미지 설명을 생성한 뒤  
심리 해석 문서 기반 RAG 시스템과 LLM을 활용하여  
상담형 심리 해석 답변을 제공하는 AI 챗봇 시스템입니다.

---


# 📁 Directory Structure

```bash

├── 📂 caption/                              # 이미지 캡셔닝 모듈
│   ├── blip_clip_models.py                  # BLIP, InstructBLIP, CLIP Interrogator 성능 비교
│   ├── kosmos2_captioning.py                # Kosmos-2 기반 이미지 캡셔닝 실험
│   ├── gpt4o_with_yolo.py                   # GPT-4o + YOLO 결합 캡셔닝
│   ├── instructblip_with_yolo.py            # InstructBLIP + YOLO 결합 실험
│   └── caption.ipynb                        # 이미지 캡셔닝 실험 노트북
│
├── 📂 computer_vision/                      # 컴퓨터 비전 및 객체 탐지
│   ├── data_preprocessing.py                # 데이터 전처리 및 구조 정리
│   ├── train_models.py                      # YOLOv8 / Detectron2 모델 학습
│   ├── test_and_evaluate.py                 # mAP 기반 모델 평가 및 테스트
│   ├── best.pt                              # 학습 완료된 YOLOv8 가중치
│   └── computer_vision.ipynb                # 객체 탐지 실험 노트북
│
├── 📂 finetunning/                          # LLM 파인튜닝 및 모델 실험
│   │
│   ├── 📂 captioning/                       # 이미지 캡션 데이터셋
│   │   ├── image_captions_blip.json
│   │   ├── image_captions_llava.json
│   │   └── image_captions_qwen.json
│   │
│   ├── 📂 layer_freezing/                   # Layer Freezing 기반 파인튜닝
│   │   ├── final_htp_model.ipynb            # 최종 Layer Freezing 모델
│   │   ├── HTP_data.jsonl                   # 학습 데이터셋
│   │   ├── interactive_test.ipynb           # 인터랙티브 테스트
│   │   └── qwen2.5-htp-layer-freeze-final/  # 학습 완료 모델
│   │
│   ├── 📂 LoRa/                             # LoRA 기반 파인튜닝
│   │   ├── LoRa.ipynb                       # LoRA 학습 실험
│   │   ├── HTP_data.jsonl                   # 학습 데이터셋
│   │   ├── htp_lora_model/                  # LoRA Adapter 모델
│   │   └── htp_merged_full_model/           # Merge 완료 모델
│   │
│   ├── 📂 combined/                         # RAG + LLM 통합 시스템
│   │   ├── rag_model_combined.ipynb         # 통합 RAG 실험
│   │   ├── htp_rag_server.py                # FastAPI 기반 RAG 서버
│   │   ├── simple_test_server.py            # 테스트 서버
│   │   └── chroma_store/                    # ChromaDB Vector Store
│   │
│   ├── Data_generation.ipynb                # 학습 데이터 생성
│   ├── test_base_model.ipynb                # 베이스 모델 성능 테스트
│   └── model_comparison_results.csv         # 모델 성능 비교 결과
│
├── 📂 RAG/                                  # Retrieval-Augmented Generation
│   │
│   ├── 📂 Chunking/                         # 문서 Chunking 전략 실험
│   │   └── 그림_심리_멀티모달_RAG.ipynb
│   │
│   ├── 📂 Embedding/                        # 임베딩 모델 파인튜닝
│   │   └── 심리_해석_임베딩_파인튜닝.ipynb
│   │
│   ├── 📂 Cross_Encoder/                    # Re-ranking 모델 실험
│   │   ├── BCE_cross_encoder.ipynb          # BCE Loss 기반 Cross Encoder
│   │   ├── margin_cross_encoder.ipynb       # Margin Loss 기반 Cross Encoder
│   │   └── 크로스_인코더_비교.ipynb          # Cross Encoder 성능 비교
│   │
│   ├── 📂 LLM/                              # LLM + RAG 통합
│   │   ├── chatbot_model.ipynb              # 챗봇 모델 실험
│   │   └── 멀티턴_멀티쿼리_history_RAG.ipynb # Multi-turn / Multi-query RAG
│   │
│   └── 📂 Web/                              # RAG 웹 API 서버
│       ├── main.py                          # FastAPI 메인 서버
│       ├── rag_engine.py                    # RAG 엔진 구현
│       └── embeddings.py                    # 임베딩 처리 모듈
│
└── 📂 web/                                  # 웹 애플리케이션
    │
    ├── 📂 web_back-main/                    # Backend (FastAPI)
    │   ├── multi_main.py                    # 메인 API 서버
    │   ├── model.py                         # LLM 모델 로딩
    │   ├── rag_engine.py                    # RAG 엔진
    │   ├── caption.py                       # 이미지 캡셔닝 처리
    │   └── Dockerfile                       # Docker 배포 환경
    │
    └── 📂 web_front-main/                   # Frontend (React / Next.js)
        └── (웹 프론트엔드 파일들)
```
---

# ✨ Main Features

## 1️⃣ Image Captioning

HTP 그림 이미지를 자연어로 설명하기 위해  
다양한 멀티모달 모델을 비교 및 실험했습니다.

### 지원 모델
- BLIP
- InstructBLIP
- Kosmos-2
- CLIP Interrogator
- GPT-4o Vision

### 주요 실험
- GPT-4o + YOLO 결합
- InstructBLIP + YOLO 결합
- 캡셔닝 모델 성능 비교

---

## 2️⃣ Computer Vision

HTP 그림 속 주요 객체를 탐지하기 위해  
YOLOv8 및 Detectron2를 활용했습니다.

### 탐지 대상
- 집(House)
- 나무(Tree)
- 사람(Person)

### 사용 모델
- YOLOv8
- Detectron2 (Faster R-CNN)

### 주요 작업
- 데이터 전처리
- 객체 탐지 모델 학습
- mAP 기반 성능 평가

---

## 3️⃣ LLM Fine-tuning

심리 해석 전문 모델 구축을 위해  
다양한 파인튜닝 기법을 실험했습니다.

### 적용 기법

| 기법 | 특징 |
|---|---|
| Layer Freezing | 일부 레이어만 학습 |
| LoRA | 적은 파라미터로 효율적 학습 |
| Full Fine-tuning | 전체 파라미터 학습 |

### 사용 모델
- Qwen 2.5 7B
- LLaVA
- BLIP-2

---

## 4️⃣ RAG System

심리학 문서 및 해석 데이터를 기반으로  
정확한 상담형 답변을 생성하기 위한 RAG 시스템을 구축했습니다.


### 주요 기술
- ChromaDB
- BGE-M3 Embedding
- Cross Encoder
- Multi-turn RAG

---

## 5️⃣ Web Application

사용자가 실제로 사용할 수 있도록  
웹 기반 챗봇 서비스를 구현했습니다.

### Backend
- FastAPI
- REST API
- Docker

### Frontend
- React
- Next.js
- Tailwind CSS

---

# 🛠 Tech Stack

## AI / ML
- PyTorch
- Transformers
- Hugging Face
- LoRA
- Sentence Transformers

## Computer Vision
- YOLOv8
- Detectron2
- BLIP
- LLaVA
- GPT-4o

## RAG
- ChromaDB
- BGE-M3
- Cross Encoder

## Backend
- FastAPI
- Python

## Frontend
- React
- Next.js
- Tailwind CSS

## DevOps
- Docker
- Runpod

---


# 📊 Project Workflow

```text
[HTP 그림 이미지 업로드]
        ↓
[YOLOv8 객체 탐지]
        ↓
[이미지 캡셔닝]
        ↓
[RAG 문서 검색]
        ↓
[Cross Encoder 재정렬]
        ↓
[LLM 심리 해석 생성]
        ↓
[웹 챗봇 응답]
```

---


# 🚀 Runpod Deployment

# Backend

```bash
git clone https://github.com/Art-Therapy-Chat/web_all.git

cd web_all/web_back-main

pip install -r requirements.txt

uvicorn multi_main:app --host 0.0.0.0 --port 8888
```

---

# Frontend

```bash
cd web_front-main

npm install

npm start
```

---

# 💻 Local Development

## Backend

```bash
cd web_back-main

pip install -r requirements.txt

uvicorn multi_main:app --reload --port 8000
```

---

## Frontend

```bash
cd web_front-main

npm install

npm start
```

---

# 📈 Result

- 멀티모달 기반 심리 상담 챗봇 구축
- 이미지 캡셔닝 + 객체 탐지 결합 실험
- RAG 기반 심리 해석 시스템 구현
- LoRA 및 Layer Freezing 기반 LLM 파인튜닝 수행
- FastAPI + React 기반 웹 서비스 구현

---

# [홈페이지]

### 전체 UI
<img width="1162" height="583" alt="image" src="https://github.com/user-attachments/assets/8c564619-bee3-4f89-8c50-b60732117a08" />

### 검사 해석 출력 및 채팅
<img width="1229" height="608" alt="image" src="https://github.com/user-attachments/assets/622bc6f9-6096-4416-9a59-3d1f0d77a919" />


