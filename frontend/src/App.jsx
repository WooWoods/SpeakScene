import {
  Bookmark,
  BookmarkCheck,
  Bot,
  CheckCircle2,
  Loader2,
  Mic,
  Play,
  Plus,
  Send,
  Trash2,
  User,
} from "lucide-react"
import { useEffect, useMemo, useRef, useState } from "react"

import {
  addTurn,
  completeSession,
  createFavorite,
  deleteFavorite,
  getFavorites,
  getHistory,
  startScenario,
  synthesizeSpeech,
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
  if (!("speechSynthesis" in window)) return
  window.speechSynthesis.cancel()
  const utterance = new SpeechSynthesisUtterance(text)
  utterance.lang = "en-US"
  utterance.rate = 0.92
  window.speechSynthesis.speak(utterance)
}

async function speak(text) {
  try {
    const audioBlob = await synthesizeSpeech(text)
    const audioUrl = URL.createObjectURL(audioBlob)
    const audio = new Audio(audioUrl)
    audio.addEventListener("ended", () => URL.revokeObjectURL(audioUrl), { once: true })
    audio.addEventListener("error", () => URL.revokeObjectURL(audioUrl), { once: true })
    await audio.play()
  } catch {
    speakWithBrowser(text)
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
  const recognitionRef = useRef(null)
  const transcriptRef = useRef(null)

  const speechSupported = useMemo(
    () => typeof window !== "undefined" && ("SpeechRecognition" in window || "webkitSpeechRecognition" in window),
    [],
  )

  const turns = session?.turns ?? []
  const canSend = Boolean(session && typedText.trim() && !sending && session.status === "active")

  async function refreshHistory() {
    try {
      setHistory(await getHistory())
    } catch {
      setHistory([])
    }
  }

  async function refreshFavorites() {
    try {
      setFavorites(await getFavorites())
    } catch {
      setFavorites([])
    }
  }

  async function loadScenario(nextLevel = level, nextCategory = category) {
    setLoading(true)
    setError("")
    setEvaluation(null)
    setTypedText("")
    try {
      const nextSession = await startScenario({ level: nextLevel, category: nextCategory })
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

  async function handleSend(inputMode = "typing") {
    const text = typedText.trim()
    if (!session || !text || sending) return
    setSending(true)
    setError("")
    try {
      const result = await addTurn({ sessionId: session.id, textEn: text, inputMode })
      setSession(result.session)
      setTypedText("")
      speak(result.system_turn.text_en)
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

  function startListening() {
    if (!speechSupported || listening) return
    const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition
    const recognition = new Recognition()
    recognition.lang = "en-US"
    recognition.interimResults = false
    recognition.maxAlternatives = 1
    recognition.onresult = (event) => {
      const transcript = event.results?.[0]?.[0]?.transcript ?? ""
      setTypedText(transcript)
    }
    recognition.onerror = () => setListening(false)
    recognition.onend = () => setListening(false)
    recognitionRef.current = recognition
    setListening(true)
    recognition.start()
  }

  function stopListening() {
    recognitionRef.current?.stop()
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
    loadScenario(3, "business")
    refreshHistory()
    refreshFavorites()
  }, [])

  useEffect(() => {
    transcriptRef.current?.scrollTo({ top: transcriptRef.current.scrollHeight, behavior: "smooth" })
  }, [turns.length])

  return (
    <main className="min-h-screen bg-skyglass text-ink">
      <div className="mx-auto flex min-h-screen w-full max-w-[1600px] flex-col px-4 py-4 sm:px-6">
        <header className="flex flex-col gap-3 border-b border-ink/10 pb-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <p className="text-sm font-semibold uppercase tracking-[0.16em] text-leaf">SpeakScene</p>
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

        <section className="grid flex-1 gap-4 py-4 xl:grid-cols-[360px_minmax(430px,1fr)_360px]">
          <aside className="rounded-lg bg-paper p-4 shadow-panel">
            <div className="flex items-center justify-between gap-3">
              <div>
                <p className="text-sm font-bold text-moss">当前场景</p>
                <h2 className="mt-1 text-xl font-black leading-tight">{session?.scenario_name ?? "Loading"}</h2>
              </div>
              <button
                type="button"
                onClick={() => loadScenario(level, category)}
                className="inline-flex h-9 items-center gap-1 rounded-md bg-leaf px-3 text-sm font-bold text-white hover:bg-leaf/90"
              >
                <Plus size={16} />
                新场景
              </button>
            </div>

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

          <section className="flex min-h-[760px] flex-col rounded-lg bg-paper p-4 shadow-panel">
            <div className="flex flex-col gap-3 border-b border-ink/10 pb-3 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <p className="text-sm font-bold text-moss">对话练习</p>
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
              {turns.map((turn) => (
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
                  </article>
                </div>
              ))}
            </div>

            <div className="border-t border-ink/10 pt-3">
              <div className="mb-3 flex flex-wrap gap-2">
                <button
                  type="button"
                  onClick={listening ? stopListening : startListening}
                  disabled={!speechSupported}
                  className="inline-flex h-9 items-center gap-2 rounded-md border border-ink/10 bg-white px-3 text-sm font-bold text-moss disabled:cursor-not-allowed disabled:text-moss/40"
                >
                  <Mic size={16} />
                  {speechSupported ? (listening ? "停止录音" : "语音输入") : "语音不可用"}
                </button>
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

          <aside className="space-y-4">
            <section className="rounded-lg bg-paper p-4 shadow-panel">
              <p className="text-sm font-bold text-moss">AI 评分</p>
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
              <p className="text-sm font-bold text-moss">收藏表达</p>
              <div className="mt-3 space-y-3">
                {favorites.length === 0 ? (
                  <p className="text-sm text-moss">点击左侧短语旁的收藏按钮后，会按场景分类保存在这里。</p>
                ) : (
                  favorites.map((group) => (
                    <div key={group.category} className="rounded-lg border border-ink/10 bg-white p-3">
                      <p className="text-xs font-black uppercase text-coral">{group.category}</p>
                      <div className="mt-2 space-y-2">
                        {group.items.map((item) => (
                          <div key={item.id} className="border-t border-ink/10 pt-2 first:border-t-0 first:pt-0">
                            <div className="flex items-start justify-between gap-2">
                              <div>
                                <p className="text-sm font-bold leading-5">{item.phrase_en}</p>
                                <p className="text-xs leading-5 text-moss">{item.phrase_cn}</p>
                              </div>
                              <button
                                type="button"
                                onClick={() => handleDeleteFavorite(item.id)}
                                className="grid h-7 w-7 shrink-0 place-items-center rounded-md border border-ink/10 text-coral"
                                title="删除收藏"
                              >
                                <Trash2 size={14} />
                              </button>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))
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
      </div>
    </main>
  )
}
