import React, { useState, useRef, useEffect, useCallback } from "react";
// 필요한 아이콘을 htp_chatbot_251116.tsx와 유사하게 조정
import { Upload, Eraser, MessageCircle, Brain, Pencil } from "lucide-react"; 

// Runpod 백엔드 서버 주소로 변경하세요
const API_BASE = process.env.REACT_APP_API_URL || "http://localhost:8000";

// 탭 이름 매핑
const tabNames = {
    house: { ko: '집', en: 'House' },
    tree: { ko: '나무', en: 'Tree' },
    person: { ko: '사람', en: 'Person' }
};

const HTPChatbot = () => {
  // 0: 사용자 정보 입력, 1: 그림 입력, 2: 결과/질문
  const [currentPage, setCurrentPage] = useState(0);
  const [userName, setUserName] = useState("");
  const [userAge, setUserAge] = useState("");
  const [userGender, setUserGender] = useState("");
  const [activeTab, setActiveTab] = useState("house");

  const [drawings, setDrawings] = useState({
    house: null,
    tree: null,
    person: null,
  });

  const [context, setContext] = useState(null);
  const canvasRef = useRef(null);

  const [isDrawing, setIsDrawing] = useState(false);
  const [brushSize, setBrushSize] = useState(2); 
  const [brushColor, setBrushColor] = useState("#000000");

  const [captions, setCaptions] = useState({
    house: "",
    tree: "",
    person: "",
  });

  const [interpretations, setInterpretations] = useState({
    house: "",
    tree: "",
    person: "",
  });
  
  // 영어 원본 해석 (질문 생성용)
  const [interpretationsEN, setInterpretationsEN] = useState({
    house: "",
    tree: "",
    person: "",
  });

  const [finalInterpretation, setFinalInterpretation] = useState("");
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState("");
  const [questionCount, setQuestionCount] = useState(0);
  const [isComplete, setIsComplete] = useState(false);
  const chatEndRef = useRef(null);
  const [isLoading, setIsLoading] = useState(false); 
  const [showLoading, setShowLoading] = useState(false);
  const loadingMessages = [
    "분석 중...",
    "그림을 꼼꼼히 확인 중...",
    "당신의 그림에 감탄 중...",
    "관련 정보를 탐색 중...",
    "논문을 읽는 중...",
    "해석을 생성하는 중..."
  ];
  const [loadingMsgIndex, setLoadingMsgIndex] = useState(0);

  useEffect(() => {
    if (!showLoading) return;
    const timer = setInterval(() => {
      setLoadingMsgIndex((i) => (i + 1) % loadingMessages.length);
    }, 2500); // 메시지가 2.5초 동안 머무르도록 설정
    return () => clearInterval(timer);
  }, [showLoading]);
  // 로딩 오버레이는 메인 렌더 내부에서 조건부로 표시합니다 (Hooks 순서 유지)
  
  /** --------------------------
   * Canvas 초기화
   * -------------------------- */
  useEffect(() => {
    if (canvasRef.current) {
      const c = canvasRef.current;
      const ctx = c.getContext("2d");
      ctx.lineWidth = brushSize;
      ctx.strokeStyle = brushColor;
      ctx.lineCap = "round";
      setContext(ctx);

      ctx.clearRect(0, 0, c.width, c.height);
      if (drawings[activeTab]) {
        const img = new Image();
        img.onload = () => ctx.drawImage(img, 0, 0);
        img.src = drawings[activeTab];
      } else {
        // 새 그림판에 기본 안내 텍스트 추가
        ctx.font = '24px Arial';
        ctx.fillStyle = '#9ca3af';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(`${tabNames[activeTab].ko}을(를) 그려주세요.`, c.width / 2, c.height / 2);
      }
    }
  }, [activeTab, brushSize, brushColor, drawings]);

  // 페이지 전환 시 캔버스 컨텍스트가 없으면 강제 초기화
  useEffect(() => {
    if (currentPage === 1 && canvasRef.current && !context) {
      const c = canvasRef.current;
      const ctx = c.getContext("2d");
      ctx.lineWidth = brushSize;
      ctx.strokeStyle = brushColor;
      ctx.lineCap = "round";
      setContext(ctx);
    }
  }, [currentPage, context, brushSize, brushColor]);

  /** --------------------------
   * Canvas 그리기 및 저장
   * -------------------------- */
  const getCoords = (e) => {
    const c = canvasRef.current;
    const rect = c.getBoundingClientRect();
    const clientX = e.clientX || (e.touches && e.touches[0].clientX);
    const clientY = e.clientY || (e.touches && e.touches[0].clientY);
    
    // 단순화된 좌표 계산 유지
    return {
      x: clientX - rect.left,
      y: clientY - rect.top,
    };
  };

  const startDraw = (e) => {
    if (!context) return;
    setIsDrawing(true);
    const { x, y } = getCoords(e);
    context.beginPath();
    context.moveTo(x, y);
    context.lineTo(x + 0.5, y + 0.5); 
    context.stroke();
  };

  const draw = (e) => {
    if (!isDrawing || !context) return;
    const { x, y } = getCoords(e);
    context.lineTo(x, y);
    context.stroke();
  };

  const endDraw = () => {
    if (!context) return;
    setIsDrawing(false);
    if (canvasRef.current) {
      const data = canvasRef.current.toDataURL();
      setDrawings((prev) => ({ ...prev, [activeTab]: data }));
    }
  };
  
  const saveCurrentDrawing = () => {
    if (canvasRef.current) {
      const data = canvasRef.current.toDataURL();
      setDrawings((prev) => ({ ...prev, [activeTab]: data }));
    }
  };

  const clearCanvas = () => {
    if (!context || !canvasRef.current) return;
    context.clearRect(0, 0, canvasRef.current.width, canvasRef.current.height);
    setDrawings((prev) => ({ ...prev, [activeTab]: null }));
    
    const c = canvasRef.current;
    context.font = '24px Arial';
    context.fillStyle = '#9ca3af';
    context.textAlign = 'center';
    context.textBaseline = 'middle';
    context.fillText(`${tabNames[activeTab].ko}을(를) 그려주세요.`, c.width / 2, c.height / 2);
  };

  /** --------------------------
   * 이미지 업로드
   * -------------------------- */
  const uploadImage = (e) => {
    const file = e.target.files[0];
    if (!file || !canvasRef.current) return;

    const reader = new FileReader();
    reader.onload = (ev) => {
      const img = new Image();
      img.onload = () => {
        const c = canvasRef.current;
        const ctx = context || c.getContext("2d");
        ctx.lineWidth = brushSize;
        ctx.strokeStyle = brushColor;
        ctx.lineCap = "round";
        setContext(ctx);
        ctx.clearRect(0, 0, c.width, c.height);
        // 이미지를 캔버스 크기에 맞게 조정하여 그리기
        ctx.drawImage(img, 0, 0, c.width, c.height); 
        setDrawings((prev) => ({
          ...prev,
          [activeTab]: c.toDataURL(),
        }));
      };
      img.src = ev.target.result;
    };
    reader.readAsDataURL(file);
    e.target.value = null; 
  };
  
  const hasAnyDrawing = () => {
    return drawings.house || drawings.tree || drawings.person;
  };

  /** --------------------------
   * 페이지 1 → 2 : 캡션 + RAG + 해석
   * -------------------------- */
  const runInterpretation = async () => {
    const tabs = ["house", "tree", "person"];
    const tabsKorean = { house: "집", tree: "나무", person: "사람" };
    const drawnTabs = tabs.filter(t => drawings[t]);

    if (drawnTabs.length === 0) {
      alert("적어도 하나의 그림을 그려주세요.");
      return;
    }
    
    setIsLoading(true);
    setShowLoading(true); // 전용 로딩 화면 표시
    setMessages([]);

    let newCaptions = {};
    let newInterps = {};
    let newInterpsEN = {}; // 영어 원본 해석 저장용 (window 대신 로컬 변수)

    for (const t of drawnTabs) {
      const base64 = drawings[t].split(",")[1];

      try {
        // 1) 캡션 생성
        const capRes = await fetch(`${API_BASE}/caption`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ image_base64: base64 }),
        });
        
        const capJson = await capRes.json();
        
        // capJson.caption: 문자열(JSON) → 객체로 파싱
        const captionObj = JSON.parse(capJson.caption); // { ko: [], en: [] }
        
        // ✅ 상태에는 한국어 배열을 문자열로 조합해서 저장 (화면 표시용)
        const koCaption = Array.isArray(captionObj.ko) 
          ? captionObj.ko.join(', ') 
          : captionObj.ko;
        newCaptions[t] = koCaption;
        
        // ✅ RAG에 한국어 캡션 리스트를 조합해서 전달
        const koForRAG = Array.isArray(captionObj.ko)
          ? captionObj.ko.join('. ')
          : captionObj.ko;
        
        const ragRes = await fetch(`${API_BASE}/rag`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            caption: koForRAG,
            image_type: tabsKorean[t],  // "집", "나무", "사람"
          }),
        });
        const ragJson = await ragRes.json();
        
        // ✅ 영어 캡션 리스트를 Qwen에 전달 (배열 그대로 또는 조합)
        const enCaption = Array.isArray(captionObj.en)
          ? captionObj.en.join('. ')
          : captionObj.en;
        console.log('Caption for interpretation:', enCaption);
        
        // 3) 개별 해석
        const intRes = await fetch(`${API_BASE}/interpret_single`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            caption: enCaption,
            rag_docs: ragJson.rag_docs || [],  // 백엔드 응답 형식에 맞춤
            image_type: tabsKorean[t],  // "집", "나무", "사람"
          }),
        });
        const intJson = await intRes.json();
        
        // ✅ 영어 원본 저장 (질문 생성용) - window 대신 로컬 변수 사용
        newInterpsEN[t] = intJson.interpretation;
        
        // 영어 해석을 한국어로 번역
        const translateRes = await fetch(`${API_BASE}/translate`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ text: intJson.interpretation }),
        });
        const translateJson = await translateRes.json();
        newInterps[t] = translateJson.translated;
        
      } catch (error) {
        console.error(`Interpretation failed for ${t}:`, error);
        const errorMsg = error.message || '알 수 없는 오류';
        newCaptions[t] = `캡션 생성 실패: ${errorMsg}`;
        newInterps[t] = `${tabNames[t].ko} 해석 중 오류가 발생했습니다.\n오류 내용: ${errorMsg}\n\n서버 상태를 확인하거나 나중에 다시 시도해주세요.`;
        // 사용자에게 알림 (첫 번째 에러만)
        if (!window.__errorAlertShown) {
          window.__errorAlertShown = true;
          alert(`${tabNames[t].ko} 처리 중 오류가 발생했습니다.\n계속 진행하거나 다시 시도할 수 있습니다.`);
        }
      }
    }

    setCaptions(newCaptions);
    setInterpretations(newInterps);
    setInterpretationsEN(newInterpsEN); // window 대신 로컬 변수 사용
    setCurrentPage(2);
    setIsLoading(false); // 분석 완료
    setShowLoading(false);
    
    // 초기 챗봇 메시지 설정 (API 호출은 생략하고 텍스트만)
    setMessages([]);
  };

  // =========================================================================================
  // [수정된 로직 시작] 첫 질문 자동 시작, 5회 제한, 최종 해석 연결
  // =========================================================================================

  // 1. [첫 질문 함수] 그림 데이터를 포함해서 요청 (useEffect보다 먼저 정의)
  const startFirstQuestion = useCallback(async () => {
    setIsLoading(true);
    setMessages([{ role: "assistant", content: "그림을 분석하여 첫 번째 질문을 생성 중입니다..." }]);

    try {
      // 백엔드에서 한국어 질문 직접 반환
      const res = await fetch(`${API_BASE}/questions`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          conversation: [],
          interpretations: interpretationsEN
        }),
      });
      const json = await res.json();

      // 번역 없이 질문 원문 직접 표시
      const questionText = (json.question || "").split("\n")[0];
      setMessages([{ role: "assistant", content: questionText }]);

    } catch (error) {
      console.error("First Question Error:", error);
      setMessages([{ role: "assistant", content: "질문을 불러오는 데 실패했습니다." }]);
    } finally {
      setIsLoading(false);
    }
  }, [interpretationsEN]);

  // useRef로 첫 질문 시작 여부 관리 (React 패턴)
  const firstQuestionStartedRef = useRef(false);
  
  // 2. [초기화] 결과 페이지(2)로 넘어왔고, 메시지가 비어있다면 첫 질문 자동 시작
  useEffect(() => {
    // currentPage가 2이고, 메시지가 없으며, 아직 완료 안 됐을 때 실행
    if (currentPage === 2 && messages.length === 0 && !isComplete) {
      const hasInterpretation = Object.values(interpretationsEN).some(v => v);
      if (hasInterpretation && !firstQuestionStartedRef.current) {
        firstQuestionStartedRef.current = true;
        startFirstQuestion();
      }
    }
  }, [currentPage, messages.length, isComplete, interpretationsEN, startFirstQuestion]);

  // 3. [메시지 전송 함수] 사용자 답변 처리 및 다음 단계 분기
  const sendMessage = async () => {
    if (!inputMessage.trim() || isComplete || isLoading) return;

    const userMsg = inputMessage;
    setInputMessage("");

    // 사용자 메시지 추가
    const newMessages = [...messages, { role: "user", content: userMsg }];
    setMessages(newMessages);
    setIsLoading(true);

    // 로딩 말풍선 미리 추가
    setMessages((prev) => [...prev, { role: "assistant", content: "..." }]);
    const loadingIndex = newMessages.length;

    try {
      const nextCount = questionCount + 1;
      setQuestionCount(nextCount);

      // ✅ [핵심 분기] 5번째 답변인지 확인
      if (nextCount < 5) {
        // 아직 질문이 남음 -> 다음 질문 생성
        await handleNextQuestion(newMessages, loadingIndex);
      } else {
        // 5번 완료 -> 질문 중단하고 최종 해석 시작
        await handleFinalInterpretation(newMessages, loadingIndex);
      }
    } catch (error) {
      console.error("Chat Error:", error);
      updateLastMessage("오류가 발생했습니다.", loadingIndex);
    } finally {
      setIsLoading(false);
    }
  };

  // 4. [다음 질문 생성] (백엔드에서 한국어로 반환)
  const handleNextQuestion = async (currentHistory, loadingIndex) => {
    try {
      // 백엔드에서 한국어 질문 직접 반환
      const res = await fetch(`${API_BASE}/questions`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ conversation: currentHistory, interpretations: interpretationsEN }),
      });
      const json = await res.json();

      // 번역 없이 질문 원문 직접 표시
      updateLastMessage(json.question || "", loadingIndex);
    } catch (error) {
      throw error;
    }
  };

  // 5. [최종 해석 생성]
  const handleFinalInterpretation = async (currentHistory, loadingIndex) => {
    updateLastMessage("모든 답변이 완료되었습니다. 최종 결과를 분석 중입니다...", loadingIndex);
    setIsLoading(true); // 로딩 유지

    try {
      const finalRes = await fetch(`${API_BASE}/interpret_final`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          single_results: interpretations,
          conversation: currentHistory,
          user_info: {
            name: userName,
            age: userAge,
            gender: userGender
          }
        }),
      });
      const finalJson = await finalRes.json();

      setFinalInterpretation(finalJson.final);
      setIsComplete(true);
      updateLastMessage("분석이 완료되었습니다. 아래의 '최종 종합 해석' 섹션을 확인하세요.", loadingIndex);
    } catch (error) {
      updateLastMessage("최종 해석 생성 중 오류가 발생했습니다.", loadingIndex);
    }
  };

  // [유틸] 메시지 내용 업데이트
  const updateLastMessage = (content, index) => {
    setMessages((prev) => {
      const updated = [...prev];
      if (updated[index]) updated[index] = { ...updated[index], content: content };
      return updated;
    });
  };

  // =========================================================================================
  // [수정된 로직 끝]
  // =========================================================================================

  /** --------------------------
   * 추가 질문
   * -------------------------- */


  useEffect(() => {
    // 메시지 스크롤
    if (chatEndRef.current)
      chatEndRef.current.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // 페이지 1 디자인
  // =========================
  // Page 0: 사용자 정보 입력
  // =========================
  if (currentPage === 0) {
    const ageValid = userAge === '' ? false : /^\d{1,3}$/.test(userAge) && parseInt(userAge) > 0 && parseInt(userAge) < 130;
    const canStart = userName.trim() !== '' && ageValid && (userGender === 'male' || userGender === 'female');
    return (
      <div className="h-screen bg-gradient-to-br from-pastel-beige to-pastel-green p-6 flex items-center justify-center">
        <div className="w-full max-w-5xl bg-white/95 backdrop-blur rounded-2xl shadow-xl p-8 grid grid-cols-1 md:grid-cols-2 gap-6 min-h-[460px]">
          {/* 좌측 로고 */}
          <div className="flex flex-col items-center justify-center h-full border-b md:border-b-0 md:border-r md:pr-6 border-sand/50 space-y-4">
            <img 
              src={process.env.PUBLIC_URL + '/로고.png'}
              onError={(e)=>{ e.currentTarget.src = process.env.PUBLIC_URL + '/logo.png'; e.currentTarget.onerror = (ev)=>{ e.currentTarget.src = process.env.PUBLIC_URL + '/logo512.png'; e.currentTarget.onerror = (ev2)=>{ e.currentTarget.src = process.env.PUBLIC_URL + '/logo192.png'; }; }; }}
              alt="서비스 로고" 
              className="w-72 h-72 md:w-96 md:h-96 object-contain drop-shadow transition-all" 
            />
          </div>
          {/* 우측 설명 및 입력 */}
          <div className="flex flex-col justify-center h-full items-center text-center">
            <h2 className="text-xl font-semibold text-ink mb-6 leading-snug">
              HTP 심리검사 챗봇 서비스입니다.<br />검사자의 정보를 입력해주세요.
            </h2>
            <div className="space-y-4 w-full max-w-sm mx-auto">
              {/* 이름 */}
              <div>
                <label className="block text-sm font-medium text-ink mb-1">이름</label>
                <input
                  type="text"
                  value={userName}
                  onChange={(e) => setUserName(e.target.value)}
                  placeholder="검사자 이름을 입력하세요"
                  className="w-full px-3 py-2 rounded-lg border border-sand bg-pastel-beige focus:outline-none focus:ring-2 focus:ring-forest text-sm text-center"
                />
              </div>
              {/* 나이 */}
              <div>
                <label className="block text-sm font-medium text-ink mb-1">나이</label>
                <input
                  type="text"
                  value={userAge}
                  onChange={(e) => setUserAge(e.target.value.replace(/[^0-9]/g,''))}
                  placeholder="숫자만 입력"
                  className="w-full px-3 py-2 rounded-lg border border-sand bg-pastel-beige focus:outline-none focus:ring-2 focus:ring-forest text-sm text-center"
                />
                {!ageValid && userAge !== '' && (
                  <p className="mt-1 text-xs text-red-500">유효한 나이를 입력해주세요 (1~129).</p>
                )}
              </div>
              {/* 성별 */}
              <div>
                <label className="block text-sm font-medium text-ink mb-2">성별</label>
                <div className="flex gap-4 flex-wrap justify-center">
                  {[
                    { value: 'female', label: '여성' },
                    { value: 'male', label: '남성' }
                  ].map(g => (
                    <label key={g.value} className={`flex items-center gap-2 px-4 py-2 rounded-lg border cursor-pointer text-sm transition ${userGender===g.value ? 'bg-pastel-yellow border-lemon shadow-sm' : 'bg-pastel-beige border-sand hover:bg-sand'}`}> 
                      <input
                        type="radio"
                        name="gender"
                        value={g.value}
                        checked={userGender === g.value}
                        onChange={(e)=>setUserGender(e.target.value)}
                        className="accent-forest"
                      />
                      {g.label}
                    </label>
                  ))}
                </div>
              </div>
            </div>
            <button
              disabled={!canStart}
              onClick={() => setCurrentPage(1)}
              className={`mt-8 w-full max-w-sm py-3 rounded-lg font-bold text-sm transition ${canStart ? 'bg-forest text-white hover:brightness-95 shadow-lg shadow-forest/30' : 'bg-pastel-beige text-ink/40 cursor-not-allowed'}`}
            >
              검사 시작
            </button>
          </div>
        </div>
      </div>
    );
  }

  // =========================
  // Page 1: 기존 그림 입력 페이지
  // =========================
  if (currentPage === 1) {
    return (
      <div className="h-screen bg-gradient-to-br from-pastel-beige to-pastel-green p-6 overflow-hidden">
        {showLoading && (
          <div className="fixed inset-0 z-50 loading-screen bg-gradient-to-br from-pastel-beige to-pastel-green relative">
            <div
              className="loading-stack flex flex-col items-center justify-end pb-24 md:pb-40"
              style={{
                backgroundImage: `url(${process.env.PUBLIC_URL + '/로딩2.png'})`,
                backgroundPosition: 'center bottom',
                backgroundRepeat: 'no-repeat',
                backgroundSize: 'contain'
              }}
              onError={(e)=>{
                e.currentTarget.style.backgroundImage = `url(${process.env.PUBLIC_URL + '/loading2.png'})`;
              }}
            >
              <div className="loading-fill">
                <img
                  src={process.env.PUBLIC_URL + '/로딩.png'}
                  onError={(e)=>{ e.currentTarget.src = process.env.PUBLIC_URL + '/loading.png'; }}
                  alt="Loading fill"
                  style={{ width: '100%', height: '100%', objectFit: 'contain', position: 'absolute', left: 0, bottom: 0, display: 'block' }}
                />
              </div>
            </div>
            {/* 메시지를 더 위로 올림 */}
            <div className="absolute bottom-44 md:bottom-52 left-0 right-0 text-center">
              <p className="text-ink text-2xl md:text-3xl font-bold animate-pulse">
                {loadingMessages[loadingMsgIndex]}
              </p>
            </div>
          </div>
        )}
        <div className="max-w-5xl mx-auto h-full flex flex-col">
          <div className="text-center mb-4">
            <h1 className="text-4xl font-bold text-forest mb-1">챗쪽이</h1>
            <h2 className="text-xl text-ink/80">HTP 심리 검사 해석 챗봇</h2>
          </div>

          <div className="bg-white/90 backdrop-blur rounded-2xl shadow-xl p-5 flex-1 flex flex-col overflow-hidden">
            {/* 탭 버튼 */}
            <div className="flex gap-2 mb-4">
              {['house', 'tree', 'person'].map((tab) => (
                <button
                  key={tab}
                  onClick={() => {
                    saveCurrentDrawing();
                    setActiveTab(tab);
                  }}
                  className={`flex-1 py-2 rounded-lg font-semibold transition-all ${
                    activeTab === tab
                      ? 'bg-forest text-white shadow-md'
                      : 'bg-pastel-beige text-forest/80 hover:bg-sand'
                  }`}
                >
                  <div className="flex flex-col items-center">
                    <span className="text-sm">{tabNames[tab].ko}</span>
                    <span className="text-xs opacity-75">{tabNames[tab].en}</span>
                  </div>
                  {drawings[tab] && (
                    <span className="ml-2 text-xs">✓</span>
                  )}
                </button>
              ))}
            </div>

            {/* 브러시 컨트롤 */}
            <div className="mb-3 flex gap-4 items-center bg-pastel-beige p-3 rounded-lg">
              <div className="flex items-center gap-2">
                <label className="text-xs font-medium text-ink/80">브러쉬 크기:</label>
                <input
                  type="range"
                  min="1"
                  max="20"
                  value={brushSize}
                  onChange={(e) => setBrushSize(Number(e.target.value))}
                  className="w-24 accent-forest"
                />
                <span className="text-xs text-ink/60 w-7">{brushSize}px</span>
              </div>
              
              <div className="flex items-center gap-2">
                <label className="text-xs font-medium text-ink/80">색상:</label>
                <input
                  type="color"
                  value={brushColor}
                  onChange={(e) => setBrushColor(e.target.value)}
                  className="w-10 h-7 rounded cursor-pointer border border-sand"
                />
              </div>
            </div>

            {/* 캔버스 */}
            <div className="mb-3 flex-1 flex items-center justify-center">
              <canvas
                ref={canvasRef}
                width={700}
                height={400}
                onMouseDown={startDraw}
                onMouseMove={draw}
                onMouseUp={endDraw}
                onMouseLeave={endDraw}
                onTouchStart={startDraw}
                onTouchMove={draw}
                onTouchEnd={endDraw}
                className="border-2 border-gray-300 rounded-lg cursor-crosshair bg-white max-w-full max-h-full"
                style={{ width: '700px', height: '400px' }} 
              />
            </div>

            {/* 액션 버튼 */}
            <div className="flex gap-3 mb-3">
              <button
                onClick={clearCanvas}
                className="flex items-center gap-2 px-3 py-2 text-sm bg-sand text-ink rounded-lg hover:bg-pastel-beige transition-colors shadow-md border border-sand"
              >
                <Eraser size={18} />
                지우기
              </button>
              <label className="flex items-center gap-2 px-3 py-2 text-sm bg-pastel-yellow text-ink rounded-lg hover:bg-lemon transition-colors cursor-pointer shadow-md border border-lemon/60">
                <Upload size={18} />
                이미지 업로드
                <input
                  type="file"
                  accept="image/*"
                  onChange={uploadImage}
                  className="hidden"
                />
              </label>
            </div>

            {/* 다음 버튼 */}
            <button
              onClick={runInterpretation}
              disabled={!hasAnyDrawing() || showLoading}
              className={`w-full py-3 rounded-lg font-bold text-base transition-all ${
                hasAnyDrawing() && !showLoading
                  ? 'bg-forest text-white hover:brightness-95 shadow-lg shadow-forest/30'
                  : 'bg-pastel-beige text-ink/40 cursor-not-allowed'
              }`}
            >
              다음 (분석)
            </button>
            
            {!hasAnyDrawing() && (
              <p className="text-center text-red-500 text-xs mt-2">
                최소 한 가지 그림을 그리거나 업로드해주세요
              </p>
            )}
          </div>
        </div>
      </div>
    );
  }

  

  // 페이지 2 디자인
  return (
    <div className="h-screen bg-gradient-to-br from-pastel-beige to-pastel-green p-4 overflow-hidden">
      <div className="max-w-7xl mx-auto h-full flex flex-col">
        {/* 헤더/처음으로 버튼 */}
        <div className="flex items-center justify-between mb-4 border-b pb-2">
          <div className="flex-1 text-center">
            <h1 className="text-3xl font-bold text-forest">검사 결과</h1>
          </div>
          <button
            onClick={() => {
              // 초기화 로직 (사용자 정보는 유지)
              setCurrentPage(0);
              setMessages([]);
              setInterpretations({ house: "", tree: "", person: "" });
              setCaptions({ house: "", tree: "", person: "" });
              setFinalInterpretation("");
              setQuestionCount(0);
              setIsComplete(false);
              setDrawings({ house: null, tree: null, person: null });
            }}
            className="px-4 py-2 bg-pastel-beige text-ink text-sm rounded-lg hover:bg-sand transition-colors shadow-sm"
          >
            처음으로 돌아가기
          </button>
        </div>

        {/* 2단 레이아웃 */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 flex-1 overflow-hidden">
          
          {/* 왼쪽: 그림 요약과 채팅창 */}
          <div className="flex flex-col gap-4 overflow-hidden">
            {/* 그림 요약 */}
            <div className="bg-white/90 backdrop-blur rounded-xl shadow-xl p-4">
              <h3 className="text-lg font-bold text-ink mb-3 flex items-center gap-2">
                <Pencil size={18} className="text-forest" />
                제출된 그림
              </h3>
              <div className="grid grid-cols-3 gap-3">
                {['house', 'tree', 'person'].map((type) => (
                  <div key={type} className="text-center">
                    <div className="mb-1">
                      <p className="font-semibold text-ink text-xs">{tabNames[type].ko}</p>
                      <p className="text-xs text-ink/60">{tabNames[type].en}</p>
                    </div>
                    <div className="border-2 border-sand rounded-lg p-2 bg-pastel-beige h-24 flex items-center justify-center">
                      {drawings[type] ? (
                        <img src={drawings[type]} alt={tabNames[type].ko} className="max-h-full max-w-full object-contain" />
                      ) : (
                        <p className="text-ink/40 text-xs">그림 없음</p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* 채팅창 */}
            <div className="bg-white/90 backdrop-blur rounded-xl shadow-xl p-4 flex flex-col flex-1 overflow-hidden">
              <h3 className="text-lg font-bold text-ink mb-3">
                {isComplete ? '추가 질문' : `추가 정보 수집 (${questionCount}/5)`}
              </h3>
              
              <div className="flex-1 overflow-y-auto mb-3 space-y-3 p-3 bg-pastel-beige rounded-lg shadow-inner">
                {messages.map((msg, idx) => (
                  <div
                    key={idx}
                    className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                  >
                    <div
                      className={`max-w-[80%] p-2 rounded-lg text-sm transition-all duration-300 ${
                        msg.role === 'user'
                          ? 'bg-forest text-white rounded-br-none' 
                          : 'bg-white border border-sand rounded-tl-none' 
                      }`}
                    >
                      <p className="whitespace-pre-wrap">{msg.content}</p>
                    </div>
                  </div>
                ))}
                {isLoading && (
                  <div className="flex justify-start">
                    <div className="bg-white border border-sand p-2 rounded-lg text-sm">
                      <p className="text-ink/60">
                        {questionCount >= 5 ? '최종 해석 생성 중...' : '질문 생성 중...'}
                      </p>
                    </div>
                  </div>
                )}
                <div ref={chatEndRef} />
              </div>

              {/* 입력창 */}
              <div className="flex gap-2">
                <input
                  type="text"
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      e.preventDefault();
                      sendMessage();
                    }
                  }}
                  placeholder={isComplete ? "궁금한 점을 물어보세요..." : "답변을 입력해주세요..."}
                  className="flex-1 px-3 py-2 text-sm border border-sand rounded-lg focus:outline-none focus:ring-2 focus:ring-forest disabled:bg-pastel-beige"
                  disabled={isLoading}
                />
                <button
                  onMouseDown={(e) => e.preventDefault()}
                  onClick={sendMessage}
                  disabled={isLoading || !inputMessage.trim()}
                  className="px-4 py-2 text-sm bg-forest text-white rounded-lg hover:brightness-95 disabled:bg-pastel-beige disabled:text-ink/40 disabled:cursor-not-allowed transition-colors shadow-md"
                >
                  전송
                </button>
              </div>
            </div>
          </div>

          {/* 오른쪽: 개별 해석과 최종 결과 */}
          <div className="flex flex-col gap-4 overflow-y-auto">
            {/* 개별 해석 */}
            <div className="bg-white/90 backdrop-blur rounded-xl shadow-xl p-4">
              <h3 className="text-lg font-bold text-ink mb-3 flex items-center gap-2">
                <Brain size={18} className="text-forest" />
                개별 해석
              </h3>
              
              {/* 집 해석 */}
              {interpretations.house && (
                <div className="mb-3 border border-sand rounded-lg p-3 bg-pastel-beige">
                  <h4 className="text-sm font-bold text-forest mb-1 flex items-center gap-2">
                    <MessageCircle className="text-forest" size={16} />
                    집 (House)
                  </h4>
                  <p className="text-sm text-ink/70 mb-2">캡션: <span className="italic">{captions.house}</span></p>
                  <div className="bg-white rounded-md p-2 text-xs whitespace-pre-wrap">
                    {interpretations.house}
                  </div>
                </div>
              )}

              {/* 나무 해석 */}
              {interpretations.tree && (
                <div className="mb-3 border border-sand rounded-lg p-3 bg-pastel-green">
                  <h4 className="text-sm font-bold text-forest mb-1 flex items-center gap-2">
                    <MessageCircle className="text-forest" size={16} />
                    나무 (Tree)
                  </h4>
                  <p className="text-sm text-ink/70 mb-2">캡션: <span className="italic">{captions.tree}</span></p>
                  <div className="bg-white rounded-md p-2 text-xs whitespace-pre-wrap">
                    {interpretations.tree}
                  </div>
                </div>
              )}

              {/* 사람 해석 */}
              {interpretations.person && (
                <div className="border border-sand rounded-lg p-3 bg-pastel-yellow">
                  <h4 className="text-sm font-bold text-forest mb-1 flex items-center gap-2">
                    <MessageCircle className="text-forest" size={16} />
                    사람 (Person)
                  </h4>
                  <p className="text-sm text-ink/70 mb-2">캡션: <span className="italic">{captions.person}</span></p>
                  <div className="bg-white rounded-md p-2 text-xs whitespace-pre-wrap">
                    {interpretations.person}
                  </div>
                </div>
              )}
            </div>

            {/* 최종 결과 */}
            {finalInterpretation && (
              <div className="bg-white/90 rounded-xl shadow-xl p-4 border-4 border-pastel-green">
                <h3 className="text-lg font-bold text-forest mb-3 flex items-center gap-2">
                  <Brain size={20} className="text-forest" />
                  최종 종합 해석
                </h3>
                <div className="bg-pastel-beige rounded-lg p-3 whitespace-pre-wrap text-sm leading-relaxed text-ink">
                  {finalInterpretation}
                </div>
              </div>
            )}
            
            {/* 최종 해석 대기 중 */}
            {!finalInterpretation && questionCount >= 1 && (
                <div className="bg-white/90 rounded-xl shadow-xl p-4 border border-sand">
                    <h3 className="text-lg font-bold text-ink/70 mb-3">최종 종합 해석 대기 중...</h3>
                    <p className="text-sm text-ink/50">추가 질문 5회를 모두 완료하면 최종 해석이 나옴.</p>
                </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default HTPChatbot;