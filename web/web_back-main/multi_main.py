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
        # RAG 문서가 리스트인지 확인
        if isinstance(req.rag_docs, list):
            # 각 문서를 요약해서 컨텍스트 구성
            ref_docs = "\n".join([f"- {str(doc)[:300]}" for doc in req.rag_docs[:3]])  # 최대 3개 문서, 각 300자
            reference_context = f"\n\nReference Literature:\n{ref_docs}"
            logger.info(f"✅ RAG 문서 {len(req.rag_docs[:3])}개를 참고하여 해석")
        else:
            logger.warning(f"⚠️  RAG 문서 형식 오류: {type(req.rag_docs)}")
    else:
        logger.info("⚠️  RAG 문서 없음 - 일반적인 HTP 원리로 해석")
    
    # 모델의 fine-tuning 형식에 맞춘 프롬프트 구조
    # instruction과 input을 명확히 분리
    result = generate_with_qwen(caption=req.caption, context=reference_context)
    
    logger.info(f"✅ [INTERPRET_SINGLE] 해석 완료")
    logger.info(f"생성된 해석: {result[:200]}..." if len(result) > 200 else f"생성된 해석: {result}")
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
    logger.info("🤖 사용 모델: (고정형 질문 모드 - LLM 호출 없음)")
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
        # 각 해석을 요약해서 포함 (너무 길면 모델 성능 저하)
        house_summary = house[:200] + "..." if len(house) > 200 else house
        tree_summary = tree[:200] + "..." if len(tree) > 200 else tree
        person_summary = person[:200] + "..." if len(person) > 200 else person
        
        interp_text = f"""
Drawing Interpretations:
- House: {house_summary}
- Tree: {tree_summary}
- Person: {person_summary}
"""

    # 모델의 fine-tuning 형식에 맞춘 간결한 프롬프트
    # 대화 히스토리가 있으면 이를 우선 고려, 없으면 해석만 사용
    if conversation_text.strip():
        context_section = f"Previous Conversation:\n{conversation_text}\n{interp_text}"
    else:
        context_section = f"Drawing Analysis:{interp_text}"
    
    # -----------------------------
    # 고정형 5개 질문 순차 반환 로직
    # -----------------------------
    FIXED_QUESTIONS = [
    "그림을 그릴 때 전반적인 기분이나 마음가짐은 어떠셨나요?",
    "그리는 동안 특별히 신경 써서 그렸거나, 반대로 그리기 망설여졌던 부분이 있었나요?",
    "그림을 완성한 직후, 가장 먼저 든 생각이나 느낌은 무엇이었나요?",
    "그리는 과정에서 감정이나 기분의 변화가 느껴지셨나요?",
    "이 그림에 대해 덧붙여 설명하거나 하고 싶은 이야기가 있나요?"
]

    # assistant 메시지 수로 현재 질문 번호 결정 (0부터 시작)
    assistant_count = sum(1 for m in req.conversation if m.get("role") == "assistant")
    question_index = assistant_count % len(FIXED_QUESTIONS)
    
    next_q = FIXED_QUESTIONS[question_index]

    logger.info(f"🧩 질문 번호: {question_index + 1}/{len(FIXED_QUESTIONS)}")
    logger.info(f"✅ [QUESTIONS] 최종 질문: {next_q}")
    logger.info("=" * 80)
    return {"question": next_q}

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
