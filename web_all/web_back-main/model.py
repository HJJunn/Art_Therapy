from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

# 전역 변수로 모델과 토크나이저를 한 번만 로드
_model = None
_tokenizer = None
_model_name = "helena29/Qwen2.5_LoRA_for_HTP"

def _load_model():
    """모델을 한 번만 로드 (싱글톤 패턴)"""
    global _model, _tokenizer
    
    if _model is None:
        print(f"🔥 Loading Qwen HTP Model: {_model_name}")
        print(f"🔍 CUDA Available: {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            print(f"🔍 CUDA Device: {torch.cuda.get_device_name(0)}")
            print(f"🔍 CUDA Memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} GB")
        
        # 토크나이저 로드
        _tokenizer = AutoTokenizer.from_pretrained(_model_name)
        
        # 모델 로드 (LoRA 어댑터가 이미 병합된 상태)
        _model = AutoModelForCausalLM.from_pretrained(
            _model_name,
            device_map="auto",
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32
        )
        
        print(f"✅ Qwen HTP Model loaded successfully!")
        print(f"✅ Model Device: {_model.device}")
    
    return _model, _tokenizer


def _clean_output(text: str) -> str:
    """
    모델 출력 후처리: 불필요한 텍스트 제거 및 불완전한 문장 처리
    """
    import re
    
    # 따옴표나 마크다운 코드 블록 제거
    text = text.strip('`"\'').strip()
    
    # "Output:", "Answer:", "Response:" 같은 프리픽스 제거
    text = re.sub(r'^(Output|Answer|Response|Result):\s*', '', text, flags=re.IGNORECASE)
    
    # 연속된 공백이나 줄바꿈 정리
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r' {2,}', ' ', text)
    
    # 불완전한 문장 감지 및 제거
    text = text.strip()
    if text and text[-1] not in '.!?。':
        # 마지막 완전한 문장 부호 찾기
        last_complete_idx = -1
        for i in range(len(text) - 1, -1, -1):
            if text[i] in '.!?。':
                last_complete_idx = i
                break
        
        # 완전한 문장이 있으면 거기까지만 유지
        if last_complete_idx > 0:
            text = text[:last_complete_idx + 1]
    
    return text.strip()


def generate_with_qwen(caption: str, context: str = ""):
    """
    Qwen 모델을 사용해 HTP 해석 생성 (Chat Template + Prefill 적용)
    """
    model, tokenizer = _load_model()
    
    # ------------------------------------------------------------------
    # [수정 1] 시스템 프롬프트와 유저 입력을 분리하여 리스트로 정의
    # ------------------------------------------------------------------
    system_prompt = """You are an expert in HTP (House-Tree-Person) projective drawing analysis. 
Analyze the provided "Drawing Observations" based on standard psychological theories.

### Constraints
1. Disclaimer: Educational purpose only. Not a medical diagnosis.
2. Format: Strictly follow the output format.
3. Tone: Analytical, objective, and empathetic.
4. Stop: Do NOT generate conversational fillers (e.g., "Here is the analysis").

### Response Format
1. Feature Analysis:
   - [Feature Name]: [Meaning]

2. Psychological Synthesis:
   [Summary]"""

    user_content = f"Drawing Observations: {caption}{context}\n\nAnalyze this strictly based on the format."

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content}
    ]

    # ------------------------------------------------------------------
    # [수정 2] apply_chat_template 사용 (모델이 이해하는 포맷으로 변환)
    # ------------------------------------------------------------------
    text_input = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True
    )
    
    # ------------------------------------------------------------------
    # [수정 3] Assistant Prefill (답변 강제 시작) - 핵심!
    # 모델이 딴소리 못하게 아예 첫 줄을 우리가 적어줍니다.
    # ------------------------------------------------------------------
    text_input += "1. Feature Analysis:\n"

    print("=" * 80)
    print(f"📝 [PROMPT] 최종 입력 프롬프트:\n{text_input}")
    print("=" * 80)

    inputs = tokenizer([text_input], return_tensors="pt").to(model.device)

    # ------------------------------------------------------------------
    # [수정 4] 생성 파라미터 최적화
    # ------------------------------------------------------------------
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=512,      # 최대 길이
            # min_new_tokens=150,    # [삭제] 억지로 길게 쓰려다 할말 없으면 소설 씁니다.
            temperature=0.1,         # [수정] 0.65 -> 0.1 (일관성 위해 매우 낮게 설정)
            top_p=0.9,
            do_sample=True,          # False로 해도 되지만, 0.1이면 True도 안전함
            repetition_penalty=1.1,  # 1.15 -> 1.1 (너무 높으면 문법 깨짐)
            
            # [수정 5] Stop Token 설정 (이상한 턴 생성 방지)
            stop_strings=["Human:", "User:", "###", "Drawing Observations:"],
            tokenizer=tokenizer      # stop_strings 사용 시 필요할 수 있음
        )

    # ------------------------------------------------------------------
    # [수정 6] 결과 후처리 (Prefill 했던 부분 다시 붙여주기)
    # ------------------------------------------------------------------
    # 입력 토큰 길이만큼 잘라냄
    input_len = inputs["input_ids"].shape[1]
    generated_ids = outputs[0][input_len:]
    decoded_output = tokenizer.decode(generated_ids, skip_special_tokens=True).strip()
    
    # 우리가 강제로 넣었던 "1. Feature Analysis:\n"가 출력엔 빠져있으므로 다시 붙임
    final_result = "1. Feature Analysis:\n" + decoded_output
    
    # 혹시 모를 뒷부분 잡동사니 제거 (2. 심리적 종합 뒷부분 자르기)
    if "2. Psychological Synthesis:" in final_result:
        # 섹션 2가 시작된 후, 줄바꿈이 3번 이상 나오면 그 뒤는 자름 (Stop token 실패 대비)
        parts = final_result.split("2. Psychological Synthesis:")
        synthesis_part = parts[1]
        # 간단한 파싱 로직: 문단이 끝나고 다른 헤더가 나오거나 너무 길어지면 자름
        # (여기서는 단순하게 유지)
        pass

    result = _clean_output(final_result)
    
    print(f"✅ [Result] Generated length: {len(result)}")
    return result