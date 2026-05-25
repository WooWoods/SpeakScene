import {
  Bookmark,
  BookmarkCheck,
  Bot,
  CheckCircle2,
  Dice5,
  Loader2,
  Mic,
  Play,
  Plus,
  Send,
  Trash2,
  User,
  Quote,
  Maximize2,
  Minimize2,
  Ear,
  EarOff,
  MessageSquare,
  BarChart2,
  Flame,
  Share2,
  BrainCircuit,
  Target,
  Award,
  X,
} from "lucide-react"
import { useEffect, useMemo, useRef, useState } from "react"
import { ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis, Radar, Tooltip } from "recharts"
import html2canvas from "html2canvas"

import {
  addTurn,
  completeSession,
  createFavorite,
  deleteFavorite,
  getFavorites,
  getHistory,
  startScenario,
  synthesizeSpeech,
  getUserProfile,
  getDailyScenario,
  reviewFavorite,
} from "./api/client"

const categories = [
  { id: "business", label: "商务" },
  { id: "travel", label: "旅行" },
  { id: "school", label: "校园" },
  { id: "restaurant", label: "餐厅" },
]

const levels = [
  { id: 1, label: "启蒙" },
  { id: 2, label: "进阶" },
  { id: 3, label: "实战" },
]

function speakWithBrowser(text) {
  return new Promise((resolve) => {
    if (!("speechSynthesis" in window)) {
      resolve()
      return
    }
    window.speechSynthesis.cancel()
    const utterance = new SpeechSynthesisUtterance(text)
    utterance.lang = "en-US"
    utterance.rate = 0.92
    utterance.onend = resolve
    utterance.onerror = resolve
    window.speechSynthesis.speak(utterance)
  })
}

async function speak(text) {
  try {
    const audioBlob = await synthesizeSpeech(text)
    const audioUrl = URL.createObjectURL(audioBlob)
    const audio = new Audio(audioUrl)
    return new Promise((resolve) => {
      audio.addEventListener("ended", () => { URL.revokeObjectURL(audioUrl); resolve() }, { once: true })
      audio.addEventListener("error", () => { URL.revokeObjectURL(audioUrl); resolve() }, { once: true })
      audio.play().catch(() => resolve())
    })
  } catch {
    return speakWithBrowser(text)
  }
}

function ScoreBar({ label, value }) {
  return (
    <div>
      <div className="mb-1 flex items-center justify-between text-xs font-bold text-moss">
        <span>{label}</span>
        <span>{value}</span>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-ink/10">
        <div className="h-full rounded-full bg-leaf" style={{ width: `${value}%` }} />
      </div>
    </div>
  )
}

export default function App() {
  const [level, setLevel] = useState(3)
  const [category, setCategory] = useState("business")
  const [session, setSession] = useState(null)
  const [typedText, setTypedText] = useState("")
  const [evaluation, setEvaluation] = useState(null)
  const [history, setHistory] = useState([])
  const [favorites, setFavorites] = useState([])
  const [loading, setLoading] = useState(false)
  const [sending, setSending] = useState(false)
  const [completing, setCompleting] = useState(false)
  const [listening, setListening] = useState(false)
  const [error, setError] = useState("")
  const [focusMode, setFocusMode] = useState(false)
  const [mobileTab, setMobileTab] = useState("chat") // "phrases", "chat", "stats"
  const [handsFreeMode, setHandsFreeMode] = useState(false)
  const [user, setUser] = useState(null)
  const [dailyChallenge, setDailyChallenge] = useState(null)
  const [showNewScenarioDialog, setShowNewScenarioDialog] = useState(false)
  const [newScenarioName, setNewScenarioName] = useState("")
  const [generatingRandom, setGeneratingRandom] = useState(false)
  const evalCardRef = useRef(null)
  
  const recognitionRef = useRef(null)
  const transcriptRef = useRef(null)
  const silenceTimerRef = useRef(null)
  
  const sessionRef = useRef(session)
  const handsFreeRef = useRef(handsFreeMode)
  const sendingRef = useRef(sending)
  const listeningRef = useRef(listening)
  
  useEffect(() => { sessionRef.current = session }, [session])
  useEffect(() => { handsFreeRef.current = handsFreeMode }, [handsFreeMode])
  useEffect(() => { sendingRef.current = sending }, [sending])
  useEffect(() => { listeningRef.current = listening }, [listening])

  const speechSupported = useMemo(
    () => typeof window !== "undefined" && ("SpeechRecognition" in window || "webkitSpeechRecognition" in window),
    [],
  )

  // Re-check speech support dynamically to handle browsers that load API after user gesture
  const isSpeechApiAvailable = useMemo(
    () => typeof window !== "undefined" && (window.SpeechRecognition || window.webkitSpeechRecognition),
    [],
  )

  // Determine if voice input is currently usable (API available + not actively listening)
  const canUseVoice = isSpeechApiAvailable && !listening

  const turns = session?.turns ?? []
  const canSend = Boolean(session && typedText.trim() && !sending && session.status === "active")

  function handleQuote(text) {
    setTypedText(prev => prev ? `${prev} ${text}` : text)
  }

  async function loadUserProfile() {
    try {
      setUser(await getUserProfile())
    } catch {}
  }

  async function loadDailyChallenge() {
    try {
      setDailyChallenge(await getDailyScenario())
    } catch {}
  }

  async function refreshHistory() {
    try {
      setHistory(await getHistory())
    } catch {
      setHistory([])
    }
  }

  const radarData = useMemo(() => {
    if (!history.length) return []
    const evals = history.map(h => h.evaluation).filter(Boolean)
    if (!evals.length) return []
    const avg = (key) => Math.round(evals.reduce((sum, e) => sum + e[key], 0) / evals.length)
    return [
      { subject: "词汇 (Vocab)", A: avg("vocabulary_score"), fullMark: 100 },
      { subject: "语法 (Grammar)", A: avg("grammar_score"), fullMark: 100 },
      { subject: "地道 (Authenticity)", A: avg("authenticity_score"), fullMark: 100 },
      { subject: "流利 (Fluency)", A: avg("fluency_score"), fullMark: 100 },
    ]
  }, [history])

  async function handleShare() {
    if (!evalCardRef.current) return
    try {
      const canvas = await html2canvas(evalCardRef.current, { scale: 2, backgroundColor: "#ffffff" })
      const link = document.createElement("a")
      link.download = `speakscene-highlight-${new Date().getTime()}.png`
      link.href = canvas.toDataURL("image/png")
      link.click()
    } catch (err) {
      console.error("Failed to generate share card", err)
    }
  }

  async function refreshFavorites() {
    try {
      setFavorites(await getFavorites())
    } catch {
      setFavorites([])
    }
  }

  async function loadScenario(nextLevel = level, nextCategory = category, scenarioName = null) {
    setLoading(true)
    setError("")
    setEvaluation(null)
    setTypedText("")
    try {
      const nextSession = await startScenario({ level: nextLevel, category: nextCategory, scenarioName })
      setSession(nextSession)
      window.setTimeout(() => {
        speak(nextSession.starter_en)
      }, 120)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  async function handleRandomScenario() {
    setGeneratingRandom(true)
    try {
      const randomCategory = categories[Math.floor(Math.random() * categories.length)].id
      const randomLevel = levels[Math.floor(Math.random() * levels.length)].id
      const nextSession = await startScenario({ level: randomLevel, category: randomCategory })
      setNewScenarioName(nextSession.scenario_name)
    } catch (err) {
      setError(err.message)
    } finally {
      setGeneratingRandom(false)
    }
  }

  async function handleSubmitNewScenario() {
    const scenarioName = newScenarioName.trim() || undefined
    setShowNewScenarioDialog(false)
    setNewScenarioName("")
    await loadScenario(level, category, scenarioName)
  }

  function handleCancelNewScenario() {
    setShowNewScenarioDialog(false)
    setNewScenarioName("")
  }

  async function handleSend(inputMode = "typing", textOverride = null) {
    const text = textOverride !== null ? textOverride.trim() : typedText.trim()
    const currentSession = sessionRef.current
    if (!currentSession || !text || sendingRef.current) return
    setSending(true)
    setError("")
    try {
      const result = await addTurn({ sessionId: currentSession.id, textEn: text, inputMode })
      setSession(result.session)
      if (textOverride === null) {
        setTypedText("")
      }
      
      await speak(result.system_turn.text_en)
      
      if (handsFreeRef.current && currentSession.status !== "completed") {
        startListening()
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setSending(false)
    }
  }

  async function handleComplete() {
    if (!session || completing) return
    setCompleting(true)
    setError("")
    try {
      const result = await completeSession({ sessionId: session.id })
      setEvaluation(result.evaluation)
      setSession((current) => current ? { ...current, status: "completed", evaluation: result.evaluation } : current)
      await refreshHistory()
      await loadUserProfile() // Refresh streak
    } catch (err) {
      setError(err.message)
    } finally {
      setCompleting(false)
    }
  }

  async function handleFavorite(phrase) {
    if (!session) return
    setError("")
    try {
      await createFavorite({
        category: session.category,
        scenario_name: session.scenario_name,
        phrase_en: phrase.en,
        phrase_cn: phrase.cn,
        usage_note_cn: phrase.usage_note_cn,
      })
      await refreshFavorites()
    } catch (err) {
      setError(err.message)
    }
  }

  async function handleDeleteFavorite(favoriteId) {
    try {
      await deleteFavorite({ favoriteId })
      await refreshFavorites()
    } catch (err) {
      setError(err.message)
    }
  }

  async function handleReviewFavorite(favoriteId, quality) {
    try {
      await reviewFavorite({ favoriteId, quality })
      await refreshFavorites()
    } catch (err) {
      setError(err.message)
    }
  }

  function startListening() {
    if (listeningRef.current) return

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
    if (!SpeechRecognition) {
      setError("语音识别不可用，请使用 Chrome 或 Edge 浏览器")
      return
    }

    const recognition = new SpeechRecognition()
    recognition.lang = "en-US"
    recognition.interimResults = true
    recognition.maxAlternatives = 1

    let currentTranscript = ""

    recognition.onresult = (event) => {
      const transcript = Array.from(event.results)
        .map((result) => result[0].transcript)
        .join("")

      currentTranscript = transcript
      setTypedText(transcript)

      if (handsFreeRef.current) {
        clearTimeout(silenceTimerRef.current)
        silenceTimerRef.current = setTimeout(() => {
          recognition.stop()
          if (currentTranscript.trim()) {
            handleSend("voice", currentTranscript)
            setTypedText("")
          }
        }, 1500)
      }
    }
    recognition.onerror = (event) => {
      setListening(false)
      if (event.error === "not-allowed") {
        setError("请允许使用麦克风权限后重试")
      } else if (event.error === "no-speech") {
        // Silent - no speech detected is not really an error worth showing
      } else if (event.error === "aborted") {
        // User stopped manually, not an error
      } else {
        setError(`语音识别错误: ${event.error}`)
      }
    }
    recognition.onend = () => {
      setListening(false)
      clearTimeout(silenceTimerRef.current)
    }
    recognitionRef.current = recognition
    setListening(true)
    setError("") // Clear any previous errors
    recognition.start()
  }

  function stopListening() {
    recognitionRef.current?.stop()
    clearTimeout(silenceTimerRef.current)
    setListening(false)
  }

  function handleLevelChange(nextLevel) {
    setLevel(nextLevel)
    loadScenario(nextLevel, category)
  }

  function handleCategoryChange(nextCategory) {
    setCategory(nextCategory)
    loadScenario(level, nextCategory)
  }

  useEffect(() => {
    loadUserProfile()
    loadDailyChallenge()
    loadScenario(3, "business")
    refreshHistory()
    refreshFavorites()
  }, [])

  useEffect(() => {
    transcriptRef.current?.scrollTo({ top: transcriptRef.current.scrollHeight, behavior: "smooth" })
  }, [turns.length])

  return (
    <main className="h-screen bg-skyglass text-ink pb-20 lg:pb-0 overflow-hidden">
      <div className="mx-auto flex h-full w-full max-w-[1600px] flex-col px-4 py-4 sm:px-6">
        <header className="shrink-0 flex flex-col gap-3 border-b border-ink/10 pb-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <div className="flex items-center gap-3">
              <p className="text-sm font-semibold uppercase tracking-[0.16em] text-leaf">SpeakScene</p>
              {user && (
                <div className="flex items-center gap-1 text-coral font-bold bg-coral/10 px-2 py-0.5 rounded-full text-xs">
                  <Flame size={14} />
                  <span>{user.streak_days} Day Streak</span>
                </div>
              )}
            </div>
            <h1 className="mt-1 text-2xl font-bold sm:text-3xl">场景短语 + AI 对话陪练</h1>
          </div>
          <div className="flex flex-wrap gap-2">
            {levels.map((item) => (
              <button
                key={item.id}
                type="button"
                onClick={() => handleLevelChange(item.id)}
                className={`h-9 rounded-md px-3 text-sm font-bold ${
                  level === item.id ? "bg-ink text-white" : "border border-ink/10 bg-white text-moss hover:border-leaf/50"
                }`}
              >
                {item.label}
              </button>
            ))}
          </div>
        </header>

        <section className={`grid flex-1 gap-4 py-4 overflow-hidden ${focusMode ? "xl:grid-cols-1 max-w-4xl mx-auto w-full" : "grid-cols-1 md:grid-cols-[280px_1fr] lg:grid-cols-[minmax(240px,280px)_minmax(340px,1fr)_minmax(240px,280px)] xl:grid-cols-[360px_minmax(430px,1fr)_360px]"}`}>
          <aside className={`rounded-lg bg-paper p-4 shadow-panel overflow-y-auto ${mobileTab === "phrases" ? "block" : "hidden"} md:block ${focusMode ? "lg:hidden" : ""}`}>
            <div className="flex items-center justify-between gap-3">
              <div>
                <p className="text-sm font-bold text-moss">当前场景</p>
                <h2 className="mt-1 text-xl font-black leading-tight">{session?.scenario_name ?? "Loading"}</h2>
              </div>
              <button
                type="button"
                onClick={() => setShowNewScenarioDialog(true)}
                className="inline-flex h-9 items-center gap-1 rounded-md bg-leaf px-3 text-sm font-bold text-white hover:bg-leaf/90"
              >
                <Plus size={16} />
                新场景
              </button>
            </div>
            {dailyChallenge && (
              <button
                type="button"
                onClick={() => {
                  handleLevelChange(dailyChallenge.level)
                  handleCategoryChange(dailyChallenge.category)
                  loadScenario(dailyChallenge.level, dailyChallenge.category)
                }}
                className="mt-3 w-full flex items-center gap-2 justify-center h-10 rounded-md bg-gradient-to-r from-coral to-leaf text-white font-bold shadow-md hover:opacity-90"
              >
                <Target size={16} />
                {dailyChallenge.scenario_name}
              </button>
            )}

            <div className="mt-4 flex flex-wrap gap-2">
              {categories.map((item) => (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => handleCategoryChange(item.id)}
                  className={`h-9 rounded-md px-3 text-sm font-bold ${
                    category === item.id
                      ? "bg-ink text-white"
                      : "border border-ink/10 bg-white text-moss hover:border-leaf/50"
                  }`}
                >
                  {item.label}
                </button>
              ))}
            </div>

            <p className="mt-4 rounded-md border border-ink/10 bg-white p-3 text-sm leading-6 text-moss">
              {session?.scenario_context_cn ?? "正在生成适合该场景的常用表达。"}
            </p>

            <div className="mt-4 space-y-3">
              <div className="flex items-center gap-2 text-sm font-bold text-moss">
                <Bookmark size={17} />
                <span>常用表达对照</span>
              </div>
              {loading ? (
                <div className="flex h-40 items-center justify-center text-sm font-bold text-moss">
                  <Loader2 className="mr-2 animate-spin" size={18} />
                  生成短语中
                </div>
              ) : (
                session?.phrases.map((phrase) => (
                  <article key={phrase.en} className="rounded-lg border border-ink/10 bg-white p-3">
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <p className="text-sm font-black leading-5">{phrase.en}</p>
                        <p className="mt-1 text-sm leading-5 text-moss">{phrase.cn}</p>
                      </div>
                        <button
                          type="button"
                          onClick={() => handleQuote(phrase.en)}
                          className="grid h-8 w-8 shrink-0 place-items-center rounded-md border border-ink/10 text-moss hover:border-leaf hover:text-leaf"
                          title="一键引用"
                        >
                          <Quote size={14} />
                        </button>
                        <button
                          type="button"
                          onClick={() => handleFavorite(phrase)}
                          className="grid h-8 w-8 shrink-0 place-items-center rounded-md border border-ink/10 text-leaf hover:border-leaf/50"
                          title="收藏表达"
                        >
                          <BookmarkCheck size={16} />
                        </button>
                      </div>
                    <div className="mt-2 flex items-center justify-between gap-2 text-xs font-bold text-moss/80">
                      <span>{phrase.usage_note_cn}</span>
                      <span className="rounded-full bg-skyglass px-2 py-1">{phrase.tone}</span>
                    </div>
                  </article>
                ))
              )}
            </div>
          </aside>

          <section className={`flex flex-col rounded-lg bg-paper p-4 shadow-panel overflow-hidden ${mobileTab === "chat" ? "block" : "hidden"} md:flex`}>
            <div className="flex flex-col gap-3 border-b border-ink/10 pb-3 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <div className="flex items-center gap-3">
                  <p className="text-sm font-bold text-moss">对话练习</p>
                  <button 
                    type="button"
                    onClick={() => setFocusMode(!focusMode)}
                    className="hidden lg:flex items-center gap-1 text-xs font-bold text-moss hover:text-ink bg-skyglass px-2 py-1 rounded-md"
                    title={focusMode ? "退出专注模式" : "专注模式"}
                  >
                    {focusMode ? <Minimize2 size={12} /> : <Maximize2 size={12} />}
                    {focusMode ? "退出专注" : "专注模式"}
                  </button>
                </div>
                <p className="mt-1 text-sm text-moss">系统先开口，用户可语音或键入回复。</p>
              </div>
              <button
                type="button"
                onClick={handleComplete}
                disabled={!session || completing || turns.filter((turn) => turn.speaker === "user").length === 0}
                className="inline-flex h-10 items-center justify-center gap-2 rounded-md bg-ink px-3 text-sm font-bold text-white disabled:cursor-not-allowed disabled:bg-moss/40"
              >
                {completing ? <Loader2 className="animate-spin" size={17} /> : <CheckCircle2 size={17} />}
                完成并评分
              </button>
            </div>

            <div ref={transcriptRef} className="flex-1 space-y-3 overflow-y-auto py-4">
              {turns.map((turn) => {
                const usedPhrases = session?.phrases?.filter(
                  (p) => turn.speaker === "user" && turn.text_en.toLowerCase().includes(p.en.toLowerCase())
                ) ?? []

                return (
                  <div key={turn.id} className={`flex ${turn.speaker === "user" ? "justify-end" : "justify-start"}`}>
                    <article
                      className={`max-w-[82%] rounded-lg p-3 ${
                        turn.speaker === "user" ? "bg-leaf text-white" : "border border-ink/10 bg-white"
                      }`}
                    >
                      <div className="mb-1 flex items-center gap-2 text-xs font-bold opacity-80">
                        {turn.speaker === "user" ? <User size={14} /> : <Bot size={14} />}
                        <span>{turn.speaker === "user" ? "You" : "System"}</span>
                        {turn.speaker === "system" ? (
                          <button
                            type="button"
                            onClick={() => speak(turn.text_en)}
                            className="ml-1 grid h-6 w-6 place-items-center rounded-md border border-current/20"
                            title="朗读"
                          >
                            <Play size={13} />
                          </button>
                        ) : null}
                      </div>
                      <p className="text-base font-bold leading-6">{turn.text_en}</p>
                      {turn.text_cn ? <p className="mt-2 text-sm leading-5 opacity-75">{turn.text_cn}</p> : null}
                      
                      {usedPhrases.length > 0 && (
                        <div className="mt-2 flex items-center gap-1 text-[10px] uppercase font-black bg-white/20 px-2 py-1 rounded-sm w-fit" title="Expression Match!">
                          <Award size={12} />
                          学以致用
                        </div>
                      )}
                    </article>
                  </div>
                )
              })}
            </div>

            <div className="shrink-0 border-t border-ink/10 pt-3">
              <div className="mb-3 flex flex-wrap gap-2 items-center justify-between">
                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={listening ? stopListening : startListening}
                    disabled={handsFreeMode && listening}
                    className={`inline-flex h-9 items-center gap-2 rounded-md border px-3 text-sm font-bold disabled:cursor-not-allowed disabled:opacity-50 ${
                      listening ? "bg-coral/10 border-coral text-coral" : "border-ink/10 bg-white text-moss hover:bg-skyglass"
                    }`}
                  >
                    {listening ? (
                      <div className="flex items-center gap-1">
                        <Mic size={16} className="animate-pulse" />
                        <div className="flex gap-[2px] items-end h-3">
                          <div className="w-1 bg-coral animate-bounce" style={{ animationDelay: "0ms" }} />
                          <div className="w-1 bg-coral animate-bounce" style={{ animationDelay: "150ms" }} />
                          <div className="w-1 bg-coral animate-bounce" style={{ animationDelay: "300ms" }} />
                        </div>
                      </div>
                    ) : (
                      <Mic size={16} />
                    )}
                    {isSpeechApiAvailable ? (listening ? "正在聆听..." : "语音输入") : "语音不可用"}
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      if (!handsFreeMode) {
                        setHandsFreeMode(true)
                        startListening()
                      } else {
                        setHandsFreeMode(false)
                        stopListening()
                      }
                    }}
                    className={`inline-flex h-9 items-center gap-1 rounded-md px-3 text-sm font-bold ${
                      handsFreeMode ? "bg-leaf text-white shadow-sm" : "bg-skyglass text-moss hover:bg-ink/5"
                    }`}
                    title="闭眼练习模式 (自动录音及发送)"
                  >
                    {handsFreeMode ? <Ear size={16} /> : <EarOff size={16} />}
                    Hands-Free
                  </button>
                </div>
              </div>

              <textarea
                value={typedText}
                onChange={(event) => setTypedText(event.target.value)}
                className="min-h-24 w-full resize-y rounded-lg border border-ink/15 bg-white p-3 text-base outline-none focus:border-leaf focus:ring-4 focus:ring-leaf/10"
                placeholder="Type your English reply..."
              />

              <div className="mt-3 flex items-center justify-between gap-3">
                {error ? <p className="text-sm font-semibold text-coral">{error}</p> : <span />}
                <button
                  type="button"
                  onClick={() => handleSend("typing")}
                  disabled={!canSend}
                  className="inline-flex h-10 items-center gap-2 rounded-md bg-leaf px-4 text-sm font-bold text-white disabled:cursor-not-allowed disabled:bg-moss/40"
                >
                  {sending ? <Loader2 className="animate-spin" size={17} /> : <Send size={17} />}
                  发送
                </button>
              </div>
            </div>
          </section>

          <aside className={`space-y-4 overflow-y-auto ${mobileTab === "stats" ? "block" : "hidden"} md:block ${focusMode ? "lg:hidden" : ""}`}>
            <section className="rounded-lg bg-paper p-4 shadow-panel" ref={evalCardRef}>
              <div className="flex items-center justify-between">
                <p className="text-sm font-bold text-moss">AI 评分</p>
                {(evaluation || session?.evaluation) && (
                  <button onClick={handleShare} className="text-leaf hover:text-leaf/80" title="生成海报">
                    <Share2 size={16} />
                  </button>
                )}
              </div>
              {evaluation || session?.evaluation ? (
                <div className="mt-4 space-y-4">
                  {(() => {
                    const result = evaluation ?? session.evaluation
                    return (
                      <>
                        <div className="rounded-lg bg-ink p-4 text-white">
                          <p className="text-sm font-semibold text-white/70">Overall</p>
                          <p className="mt-1 text-5xl font-black">{result.overall_score}</p>
                        </div>
                        <div className="space-y-3 rounded-lg border border-ink/10 bg-white p-4">
                          <ScoreBar label="Vocabulary" value={result.vocabulary_score} />
                          <ScoreBar label="Grammar" value={result.grammar_score} />
                          <ScoreBar label="Authenticity" value={result.authenticity_score} />
                          <ScoreBar label="Fluency" value={result.fluency_score} />
                        </div>
                        <p className="rounded-lg border border-ink/10 bg-white p-3 text-sm leading-6 text-moss">
                          {result.feedback_cn}
                        </p>
                        <div className="rounded-lg border border-ink/10 bg-white p-3">
                          <p className="text-sm font-bold">建议表达</p>
                          <div className="mt-2 space-y-2">
                            {result.suggested_phrases.map((phrase) => (
                              <p key={phrase.en} className="text-sm leading-5 text-moss">
                                <strong className="text-ink">{phrase.en}</strong> · {phrase.cn}
                              </p>
                            ))}
                          </div>
                        </div>
                      </>
                    )
                  })()}
                </div>
              ) : (
                <p className="mt-4 rounded-lg border border-dashed border-ink/20 bg-white p-4 text-sm leading-6 text-moss">
                  完成一次对话后，这里会显示词汇、语法、地道度和流畅度评分。
                </p>
              )}
            </section>

            <section className="rounded-lg bg-paper p-4 shadow-panel">
              <div className="flex items-center gap-2 text-sm font-bold text-moss mb-3">
                <BrainCircuit size={17} />
                <span>收藏与复习 (SRS)</span>
              </div>
              <div className="space-y-3">
                {favorites.length === 0 ? (
                  <p className="text-sm text-moss">暂无收藏。收藏短语后可在此进行间隔重复复习。</p>
                ) : (
                  favorites.map((group) => {
                    const now = new Date().getTime()
                    const dueItems = group.items.filter(item => new Date(item.next_review_date).getTime() <= now)
                    const notDueItems = group.items.filter(item => new Date(item.next_review_date).getTime() > now)
                    
                    return (
                      <div key={group.category} className="rounded-lg border border-ink/10 bg-white p-3">
                        <p className="text-xs font-black uppercase text-coral">{group.category} ({dueItems.length} Due)</p>
                        <div className="mt-2 space-y-3">
                          {dueItems.map((item) => (
                            <div key={item.id} className="border border-coral/30 bg-coral/5 p-2 rounded-md">
                              <div className="flex items-start justify-between gap-2">
                                <div className="flex-1">
                                  <p className="text-xs font-semibold text-coral mb-1">Due for review!</p>
                                  <p className="text-sm font-bold leading-5">{item.phrase_en}</p>
                                  <p className="text-xs leading-5 text-moss">{item.phrase_cn}</p>
                                </div>
                                <button type="button" onClick={() => handleDeleteFavorite(item.id)} className="text-coral">
                                  <Trash2 size={14} />
                                </button>
                              </div>
                              <div className="mt-2 flex gap-1">
                                <button onClick={() => handleReviewFavorite(item.id, 1)} className="flex-1 text-[10px] font-bold bg-white border border-ink/10 py-1 rounded hover:bg-ink/5">Hard</button>
                                <button onClick={() => handleReviewFavorite(item.id, 3)} className="flex-1 text-[10px] font-bold bg-white border border-ink/10 py-1 rounded hover:bg-ink/5">Good</button>
                                <button onClick={() => handleReviewFavorite(item.id, 5)} className="flex-1 text-[10px] font-bold bg-white border border-ink/10 py-1 rounded hover:bg-ink/5 text-leaf">Easy</button>
                              </div>
                            </div>
                          ))}
                          {notDueItems.map((item) => (
                            <div key={item.id} className="border-t border-ink/10 pt-2 first:border-t-0 first:pt-0">
                              <div className="flex items-start justify-between gap-2">
                                <div>
                                  <p className="text-sm font-bold leading-5">{item.phrase_en}</p>
                                  <p className="text-xs leading-5 text-moss">{item.phrase_cn}</p>
                                  <p className="text-[10px] text-moss/60 mt-1">Next review: {new Date(item.next_review_date).toLocaleDateString()}</p>
                                </div>
                                <button type="button" onClick={() => handleDeleteFavorite(item.id)} className="grid h-7 w-7 shrink-0 place-items-center rounded-md border border-ink/10 text-coral">
                                  <Trash2 size={14} />
                                </button>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )
                  })
                )}
              </div>
            </section>
            
            <section className="rounded-lg bg-paper p-4 shadow-panel">
              <p className="text-sm font-bold text-moss">能力雷达图 (Fluency Radar)</p>
              <div className="mt-3 h-48 w-full bg-white border border-ink/10 rounded-lg">
                {radarData.length > 0 ? (
                  <ResponsiveContainer width="100%" height="100%">
                    <RadarChart cx="50%" cy="50%" outerRadius="70%" data={radarData}>
                      <PolarGrid />
                      <PolarAngleAxis dataKey="subject" tick={{ fontSize: 10, fill: '#6b7280' }} />
                      <Tooltip />
                      <Radar name="Score" dataKey="A" stroke="#10b981" fill="#10b981" fillOpacity={0.3} />
                    </RadarChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="flex h-full items-center justify-center text-sm text-moss">暂无足够数据</div>
                )}
              </div>
            </section>

            <section className="rounded-lg bg-paper p-4 shadow-panel">
              <p className="text-sm font-bold text-moss">最近对话</p>
              <div className="mt-3 space-y-2">
                {history.length === 0 ? (
                  <p className="text-sm text-moss">完成第一段对话后，这里会显示记录。</p>
                ) : (
                  history.slice(0, 5).map((item) => (
                    <article key={item.id} className="rounded-md border border-ink/10 bg-white p-3">
                      <div className="flex items-center justify-between gap-3">
                        <p className="line-clamp-1 text-sm font-bold">{item.scenario_name}</p>
                        <span className="rounded-full bg-leaf/10 px-2 py-1 text-xs font-black text-leaf">
                          {item.evaluation?.overall_score ?? item.status}
                        </span>
                      </div>
                      <p className="mt-1 line-clamp-1 text-xs text-moss">{item.scenario_context_cn}</p>
                    </article>
                  ))
                )}
              </div>
            </section>
          </aside>
        </section>
        
        {/* Mobile Bottom Navigation Tabs */}
        <nav className="lg:hidden fixed bottom-0 left-0 right-0 bg-white border-t border-ink/10 flex items-center justify-around z-50 px-2 py-2 safe-area-bottom">
          <button
            onClick={() => setMobileTab("phrases")}
            className={`flex flex-col items-center gap-1 p-2 rounded-md flex-1 ${mobileTab === "phrases" ? "text-leaf" : "text-moss"}`}
          >
            <Bookmark size={20} />
            <span className="text-[10px] font-bold">短语</span>
          </button>
          <button
            onClick={() => setMobileTab("chat")}
            className={`flex flex-col items-center gap-1 p-2 rounded-md flex-1 ${mobileTab === "chat" ? "text-leaf" : "text-moss"}`}
          >
            <MessageSquare size={20} />
            <span className="text-[10px] font-bold">对话</span>
          </button>
          <button
            onClick={() => setMobileTab("stats")}
            className={`flex flex-col items-center gap-1 p-2 rounded-md flex-1 ${mobileTab === "stats" ? "text-leaf" : "text-moss"}`}
          >
            <BarChart2 size={20} />
            <span className="text-[10px] font-bold">复盘</span>
          </button>
        </nav>

        {/* New Scenario Dialog */}
        {showNewScenarioDialog && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-ink/50 backdrop-blur-sm">
            <div className="w-full max-w-md rounded-xl bg-paper p-6 shadow-2xl">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-black text-ink">创建新场景</h3>
                <button
                  type="button"
                  onClick={handleCancelNewScenario}
                  className="grid h-8 w-8 place-items-center rounded-full hover:bg-ink/10"
                >
                  <X size={18} className="text-moss" />
                </button>
              </div>
              <div className="space-y-4">
                <div>
                  <label className="mb-1.5 block text-sm font-bold text-moss">场景名称（可选）</label>
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={newScenarioName}
                      onChange={(e) => setNewScenarioName(e.target.value)}
                      placeholder="留空则由 AI 自动生成"
                      className="flex-1 rounded-lg border border-ink/15 bg-white px-3 py-2.5 text-sm outline-none focus:border-leaf focus:ring-4 focus:ring-leaf/10"
                    />
                    <button
                      type="button"
                      onClick={handleRandomScenario}
                      disabled={generatingRandom}
                      className="inline-flex h-11 items-center gap-2 rounded-lg border border-ink/15 bg-white px-3 text-sm font-bold text-moss hover:bg-skyglass disabled:opacity-50"
                      title="随机生成场景"
                    >
                      {generatingRandom ? <Loader2 size={16} className="animate-spin" /> : <Dice5 size={16} />}
                      随机
                    </button>
                  </div>
                </div>
                <div className="flex justify-end gap-3 pt-2">
                  <button
                    type="button"
                    onClick={handleCancelNewScenario}
                    className="h-10 rounded-lg border border-ink/15 px-4 text-sm font-bold text-moss hover:bg-ink/5"
                  >
                    取消
                  </button>
                  <button
                    type="button"
                    onClick={handleSubmitNewScenario}
                    className="h-10 rounded-lg bg-leaf px-4 text-sm font-bold text-white hover:bg-leaf/90"
                  >
                    开始练习
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </main>
  )
}
