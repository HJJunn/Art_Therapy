from dotenv import load_dotenv
load_dotenv()
from embeddings import vectorstore           # 벡터 DB
from rag_engine import AdvancedConversationalRAG  # 멀티쿼리 RAG 엔진

from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional, Dict, Any
from caption import generate_caption
from model import generate_with_qwen
from fastapi.middleware.cors import CORSMiddleware
import logging
import json

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI()
# CORS 설정 - 더 명시적으로 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 모든 출처 허용
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)

# -------------------------------------
# RAG 엔진 초기화
# -------------------------------------
rag = AdvancedConversationalRAG(vectorstore)

# ----------------------------- #
# 1) 이미지 캡션 생성
# ----------------------------- #
class CaptionRequest(BaseModel):
    image_base64: str

@app.post("/caption")
def caption(req: CaptionRequest):
    logger.info("=" * 80)
    logger.info("📸 [CAPTION] 이미지 캡션 생성 시작")
    logger.info("🤖 사용 모델: Florence-2-large")
    logger.info(f"입력 이미지 크기: {len(req.image_base64)} bytes")
    
    caption = generate_caption(req.image_base64)
    
    logger.info(f"✅ [CAPTION] 생성된 캡션: {caption}")
    logger.info("=" * 80)
    return {"caption": caption}

# ----------------------------- #
# 2) 멀티쿼리 기반 RAG 검색
# ----------------------------- #
class RagRequest(BaseModel):
    caption: str
    image_type: str    # "집" | "나무" | "사람"

@app.post("/rag")
def rag_search_api(req: RagRequest):
    logger.info("=" * 80)
    logger.info("🔍 [RAG] RAG 검색 시작 (검색 전용 모드)")
    logger.info("🤖 쿼리 재작성 모델: GPT-4o (OpenAI)")
    logger.info(f"입력 캡션: {req.caption}")
    logger.info(f"이미지 타입: {req.image_type}")
    
    try:
        # search_only 메서드 사용 (해석 생성 제거)
        result = rag.search_only(req.caption, req.image_type)
        
        logger.info(f"✅ [RAG] 검색 완료")
        logger.info(f"재작성된 쿼리: {result.get('rewritten_queries', [])}")
        logger.info(f"검색된 문서 수: {len(result.get('rag_docs', []))}")
        
        # 각 문서의 내용 출력
        for idx, doc in enumerate(result.get('rag_docs', []), 1):
            logger.info(f"\n📄 문서 {idx}:")
            logger.info(f"  내용: {doc[:200]}..." if len(doc) > 200 else f"  내용: {doc}")
        
        logger.info("=" * 80)
        return result
        
    except Exception as e:
        logger.error(f"❌ [RAG] 검색 실패: {str(e)}")
        logger.error(f"에러 타입: {type(e).__name__}")
        import traceback
        logger.error(f"스택 트레이스:\n{traceback.format_exc()}")
        logger.info("=" * 80)
        
        # 빈 결과 반환 (에러 발생 시)
        return {
            "rewritten_queries": [req.caption],
            "rag_docs": [],
            "error": str(e)
        }

# ----------------------------- #
# 3) Qwen 로라 모델 개별 해석
# ----------------------------- #
class InterpretSingle(BaseModel):
    caption: str
    rag_docs: list
    image_type: str

@app.post("/interpret_single")
def interpret_single(req: InterpretSingle):
    logger.info("=" * 80)
    logger.info("🧠 [INTERPRET_SINGLE] 개별 해석 시작")
    logger.info("🤖 사용 모델: Qwen (helena29/Qwen2.5_LoRA_for_HTP)")
    logger.info(f"이미지 타입: {req.image_type}")
    logger.info(f"입력 캡션: {req.caption}")
    logger.info(f"RAG 문서 수: {len(req.rag_docs)}")
    
    # RAG 문서가 있으면 참고문헌으로 활용
    reference_context = ""
    if req.rag_docs and len(req.rag_docs) > 0:
        reference_context = f"\n\nReference Literature (Korean):\n{' '.join(req.rag_docs)}"
        logger.info("✅ RAG 문서를 참고하여 해석")
    else:
        logger.info("⚠️  RAG 문서 없음 - 일반적인 HTP 원리로 해석")
    
    # 모델의 fine-tuning 형식에 맞춘 프롬프트 구조
    prompt = f"""Please provide a psychological interpretation of the following HTP test image caption.

Drawing Type: {req.image_type}
Caption: {req.caption}{reference_context}

Provide a detailed psychological interpretation analyzing the visual features and their psychological significance. Structure your response as:

1. **Feature Analysis**: Identify and interpret specific visual elements from the caption (e.g., size, placement, details, omissions).
2. **Psychological Synthesis**: Integrate these features into a comprehensive psychological assessment of emotional state, personality traits, and coping mechanisms.

Use professional psychological terminology and maintain an analytical, empathetic tone. Write the response in English."""
    
    logger.info(f"\n📝 프롬프트 길이: {len(prompt)} characters")

    result = generate_with_qwen(prompt)
    
    logger.info(f"✅ [INTERPRET_SINGLE] 해석 완료")
    logger.info(f"생성된 해석: {result}")
    logger.info("=" * 80)
    return {"interpretation": result}

# ----------------------------- #
# 4) GPT 번역 API
# ----------------------------- #
from openai import OpenAI
client = OpenAI()

class TranslateRequest(BaseModel):
    text: str

@app.post("/translate")
def translate(req: TranslateRequest):
    """영어 텍스트를 한국어로 번역"""
    logger.info("🌐 [TRANSLATE] 번역 시작")
    logger.info(f"원문 (영어): {req.text[:100]}...")
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a professional translator. Translate the given English text to natural Korean. Only provide the translation, nothing else."},
                {"role": "user", "content": req.text}
            ],
            temperature=0.3
        )
        
        translated = response.choices[0].message.content
        logger.info(f"번역 결과 (한국어): {translated[:100]}...")
        return {"translated": translated}
        
    except Exception as e:
        logger.error(f"❌ [TRANSLATE] 번역 실패: {str(e)}")
        return {"translated": req.text}  # 실패시 원문 반환

# ----------------------------- #
# 5) Qwen 모델로 추가 질문 생성 (영어)
# ----------------------------- #

class QuestionReq(BaseModel):
    conversation: list
    interpretations: Optional[Dict[str, Any]] = None  # { house: str, tree: str, person: str }

@app.post("/questions")
def questions(req: QuestionReq):
    logger.info("=" * 80)
    logger.info("❓ [QUESTIONS] 추가 질문 생성 시작")
    logger.info("🤖 사용 모델: Qwen (helena29/Qwen2.5_LoRA_for_HTP)")
    logger.info(f"대화 기록 수: {len(req.conversation)}")
    
    for idx, msg in enumerate(req.conversation[-3:], 1):  # 최근 3개만 로깅
        logger.info(f"  메시지 {idx}: {msg.get('role')} - {msg.get('content')[:100]}...")
    
    # 대화 히스토리를 프롬프트로 변환
    conversation_text = "\n".join([
        f"{msg.get('role').upper()}: {msg.get('content')}" 
        for msg in req.conversation
    ])

    # 해석 컨텍스트(있는 경우) 포함
    interp_text = ""
    if req.interpretations:
        house = req.interpretations.get("house", "")
        tree = req.interpretations.get("tree", "")
        person = req.interpretations.get("person", "")
        interp_text = (
            "\nHTP Individual Interpretations (Korean):\n"
            f"- House: {house}\n"
            f"- Tree: {tree}\n"
            f"- Person: {person}\n"
        )

    prompt = f"""
You are a professional psychologist conducting an HTP (House-Tree-Person) assessment interview.

Conversation History:
{conversation_text}
{interp_text}

Task: Ask exactly ONE concrete follow-up question (English) that probes observable drawing decisions and missing elements related to the HTP drawings.

Strict Requirements:
- One sentence only, must end with a question mark.
- Refer explicitly to the drawing (House/Tree/Person) or a concrete feature inferred from the interpretation text.
- Focus on drawing-specific clarifications, such as:
  • reason for emphasizing/omitting a feature (chimney, windows, roots, hands/feet, etc.)
  • placement on the page (top/bottom/left/right, margins)
  • size/proportion or balance (very small/large, centered, crowded/empty background)
  • line quality/pressure or shading (pressed hard, repeated strokes)
  • order of drawing or number of erasures/redo actions
- Do NOT ask meta/process questions (e.g., “Shall I continue?”, “Provide more context”).
- Do NOT ask about the test procedure itself; ask about the drawing choices and feelings during drawing.
- No preambles, no explanations, output only the question.
"""
    
    result = generate_with_qwen(prompt)

    # 결과 후처리: 한 문장(질문부호로 끝나는)만 반환
    try:
        import re

        text = (result or "").strip()
        # 줄바꿈/불릿/번호 제거
        text = re.sub(r"^[\-\d\.)\s]+", "", text)
        # 처음 물음표가 나올 때까지의 문장만 취득
        m = re.search(r"(.+?\?)", text, flags=re.S)
        if m:
            cleaned = m.group(1)
        else:
            # 물음표가 없다면 첫 줄만 사용, 길이 제한
            cleaned = text.splitlines()[0] if text else ""
            cleaned = cleaned[:200]
        cleaned = cleaned.strip().strip('"“”')
    except Exception as e:
        logger.warning(f"[QUESTIONS] 후처리 중 오류: {e}")
        cleaned = result

    logger.info(f"✅ [QUESTIONS] 최종 질문: {cleaned}")
    logger.info("=" * 80)
    return {"question": cleaned}

# ----------------------------- #
# 6) 최종 해석 (GPT-4o)
# ----------------------------- #
class InterpretFinal(BaseModel):
    single_results: dict
    conversation: list
    user_info: Optional[Dict[str, Any]] = None  # { name: str, age: str/int, gender: 'male'|'female' }

@app.post("/interpret_final")
def interpret_final(req: InterpretFinal):
    logger.info("=" * 80)
    logger.info("🎯 [INTERPRET_FINAL] 최종 해석 생성 시작")
    logger.info("🤖 사용 모델: GPT-4o (OpenAI)")
    logger.info(f"집 해석: {req.single_results.get('house', '없음')[:100]}...")
    logger.info(f"나무 해석: {req.single_results.get('tree', '없음')[:100]}...")
    logger.info(f"사람 해석: {req.single_results.get('person', '없음')[:100]}...")
    logger.info(f"대화 기록 수: {len(req.conversation)}")
    
    # 사용자 정보 반영
    name = None
    age = None
    gender = None
    if req.user_info:
        name = req.user_info.get('name')
        age = req.user_info.get('age')
        gender = req.user_info.get('gender')

    # 성별/나이 설명 문구 구성 (해석 참고용)
    demo_context_lines = []
    if age:
        demo_context_lines.append(f"- 검사자의 나이: {age} (발달 단계 및 연령 특성을 고려해 해석에 참고)\n")
    if gender:
        ko_gender = '여성' if str(gender).lower() == 'female' else ('남성' if str(gender).lower() == 'male' else str(gender))
        demo_context_lines.append(f"- 검사자의 성별: {ko_gender} (성별에 따른 일반적 경향을 참고하되, 고정관념은 피할 것)\n")
    demo_context = "".join(demo_context_lines)

    # GPT 메시지 구성
    messages = [
        {
            "role": "system",
            "content": "You are a professional psychological counselor specializing in HTP (House-Tree-Person) test interpretation. Provide comprehensive, insightful psychological analysis in Korean."
        },
        {
            "role": "user",
            "content": f"""
당신은 전문 심리상담사입니다. 아래 HTP 검사 결과를 종합하여 최종 심리 해석을 작성해주세요.

집 해석 (House Interpretation):
{req.single_results.get('house','N/A')}

나무 해석 (Tree Interpretation):
{req.single_results.get('tree','N/A')}

사람 해석 (Person Interpretation):
{req.single_results.get('person','N/A')}

사용자와 나눈 대화:
{req.conversation}

검사자 정보:
{('- 이름: ' + str(name) + '\n') if name else ''}{demo_context}

위 정보를 종합하여 최종 HTP 심리 해석을 5개 문단으로 작성하세요.

중요 지침:
- 반드시 한국어로 작성하세요
- 각 그림(집, 나무, 사람)의 개별 해석을 통합하여 전체적인 심리 상태를 분석하세요
- 사용자와의 대화 내용을 참고하여 더 깊이 있는 해석을 제공하세요
- 전문적이고 따뜻한 어조로 작성하세요
- 5개 문단으로 구성하세요
"""
        }
    ]
    
    logger.info(f"📝 GPT 요청 전송 중...")
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        temperature=0.7,
        max_tokens=2000
    )
    
    result = response.choices[0].message.content
    
    logger.info(f"✅ [INTERPRET_FINAL] 최종 해석 완료")
    logger.info(f"생성된 최종 해석 (처음 200자): {result[:200]}...")
    logger.info("=" * 80)
    return {"final": result}
