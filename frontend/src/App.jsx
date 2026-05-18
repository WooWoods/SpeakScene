import { BookOpen, CheckCircle2, Lightbulb, Loader2, RotateCcw, Send } from "lucide-react"
import { useEffect, useMemo, useState } from "react"

import { generateTask, getDueReviews, getHints, getHistory, markMastered, submitAnswer } from "./api/client"
import { FeedbackPanel } from "./components/FeedbackPanel"
import { KeywordCard } from "./components/KeywordCard"
import { LevelTabs } from "./components/LevelTabs"
import { ReviewQueue } from "./components/ReviewQueue"

const categories = [
  { id: "business", label: "商务" },
  { id: "travel", label: "旅行" },
  { id: "school", label: "校园" },
  { id: "restaurant", label: "餐厅" },
]

export default function App() {
  const [level, setLevel] = useState(3)
  const [category, setCategory] = useState("business")
  const [task, setTask] = useState(null)
  const [answer, setAnswer] = useState("")
  const [feedback, setFeedback] = useState(null)
  const [hints, setHints] = useState(null)
  const [history, setHistory] = useState([])
  const [reviews, setReviews] = useState([])
  const [loading, setLoading] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState("")

  const canSubmit = useMemo(() => Boolean(task && answer.trim() && !submitting), [answer, submitting, task])

  async function loadTask(nextLevel = level, nextCategory = category) {
    setLoading(true)
    setError("")
    setFeedback(null)
    setHints(null)
    setAnswer("")
    try {
      const nextTask = await generateTask({ level: nextLevel, category: nextCategory })
      setTask(nextTask)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  async function refreshHistory() {
    try {
      const rows = await getHistory()
      setHistory(rows)
    } catch {
      setHistory([])
    }
  }

  async function refreshReviews() {
    try {
      const rows = await getDueReviews()
      setReviews(rows)
    } catch {
      setReviews([])
    }
  }

  async function handleSubmit(event) {
    event.preventDefault()
    if (!canSubmit) return

    setSubmitting(true)
    setError("")
    try {
      const result = await submitAnswer({ taskId: task.id, userInput: answer.trim() })
      setFeedback(result.feedback)
      await refreshHistory()
      await refreshReviews()
    } catch (err) {
      setError(err.message)
    } finally {
      setSubmitting(false)
    }
  }

  async function handleMarkMastered(attemptId) {
    try {
      await markMastered({ attemptId })
      await refreshReviews()
      await refreshHistory()
    } catch (err) {
      setError(err.message)
    }
  }

  async function handleHints() {
    if (!task) return
    setError("")
    try {
      const result = await getHints({ taskId: task.id })
      setHints(result)
    } catch (err) {
      setError(err.message)
    }
  }

  function handleLevelChange(nextLevel) {
    setLevel(nextLevel)
    loadTask(nextLevel, category)
  }

  function handleCategoryChange(nextCategory) {
    setCategory(nextCategory)
    loadTask(level, nextCategory)
  }

  useEffect(() => {
    loadTask(3, "business")
    refreshHistory()
    refreshReviews()
  }, [])

  return (
    <main className="min-h-screen bg-skyglass text-ink">
      <div className="mx-auto flex min-h-screen w-full max-w-7xl flex-col px-4 py-4 sm:px-6 lg:px-8">
        <header className="flex flex-col gap-4 border-b border-ink/10 pb-4 md:flex-row md:items-center md:justify-between">
          <div>
            <p className="text-sm font-semibold uppercase tracking-[0.16em] text-leaf">SpeakScene</p>
            <h1 className="mt-1 text-2xl font-bold sm:text-3xl">开口境 AI 情境英语陪练</h1>
          </div>
          <LevelTabs value={level} onChange={handleLevelChange} />
        </header>

        <section className="grid flex-1 gap-4 py-4 lg:grid-cols-[minmax(0,1.05fr)_minmax(360px,0.95fr)]">
          <div className="rounded-lg bg-paper p-4 shadow-panel sm:p-6">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <div className="flex items-center gap-2 text-sm font-semibold text-moss">
                <BookOpen size={18} />
                <span>今日练习</span>
              </div>
              <div className="flex flex-wrap gap-2">
                {categories.map((item) => (
                  <button
                    key={item.id}
                    type="button"
                    onClick={() => handleCategoryChange(item.id)}
                    className={`h-9 rounded-md px-3 text-sm font-semibold transition ${
                      category === item.id
                        ? "bg-ink text-white"
                        : "border border-ink/10 bg-white text-moss hover:border-leaf/50"
                    }`}
                  >
                    {item.label}
                  </button>
                ))}
              </div>
            </div>

            {loading ? (
              <div className="mt-12 flex min-h-[360px] items-center justify-center text-moss">
                <Loader2 className="mr-2 animate-spin" size={22} />
                正在生成情境任务
              </div>
            ) : task ? (
              <>
                <div className="mt-6 rounded-lg border border-ink/10 bg-white p-4">
                  <p className="text-sm font-semibold text-coral">{task.task_name}</p>
                  <p className="mt-2 text-base text-moss">{task.context_cn}</p>
                  <p className="mt-4 text-2xl font-bold leading-snug">{task.cn_sentence}</p>
                </div>

                <div className="mt-5 grid gap-3 sm:grid-cols-3">
                  {task.keywords.map((keyword) => (
                    <KeywordCard key={keyword.text} keyword={keyword} />
                  ))}
                </div>

                <form className="mt-5" onSubmit={handleSubmit}>
                  <label className="text-sm font-semibold text-moss" htmlFor="answer">
                    Your English
                  </label>
                  <textarea
                    id="answer"
                    value={answer}
                    onChange={(event) => setAnswer(event.target.value)}
                    className="mt-2 min-h-36 w-full resize-y rounded-lg border border-ink/15 bg-white p-4 text-lg outline-none transition focus:border-leaf focus:ring-4 focus:ring-leaf/10"
                    placeholder="Try to say it in English..."
                  />

                  <div className="mt-4 flex flex-wrap gap-3">
                    <button
                      type="submit"
                      disabled={!canSubmit}
                      className="inline-flex h-11 items-center rounded-md bg-leaf px-4 text-sm font-bold text-white transition hover:bg-leaf/90 disabled:cursor-not-allowed disabled:bg-moss/40"
                    >
                      {submitting ? <Loader2 className="mr-2 animate-spin" size={18} /> : <Send className="mr-2" size={18} />}
                      提交点评
                    </button>
                    <button
                      type="button"
                      onClick={handleHints}
                      className="inline-flex h-11 items-center rounded-md border border-ink/10 bg-white px-4 text-sm font-bold text-moss transition hover:border-coral/50"
                    >
                      <Lightbulb className="mr-2" size={18} />
                      查看提示
                    </button>
                    <button
                      type="button"
                      onClick={() => loadTask(level, category)}
                      className="inline-flex h-11 items-center rounded-md border border-ink/10 bg-white px-4 text-sm font-bold text-moss transition hover:border-leaf/50"
                    >
                      <RotateCcw className="mr-2" size={18} />
                      换一句
                    </button>
                  </div>
                </form>
              </>
            ) : null}

            {error ? <p className="mt-4 rounded-md bg-coral/10 p-3 text-sm font-semibold text-coral">{error}</p> : null}
          </div>

          <aside className="flex flex-col gap-4">
            <FeedbackPanel feedback={feedback} hints={hints} />
            <ReviewQueue
              items={reviews}
              onMarkMastered={handleMarkMastered}
              onRefresh={refreshReviews}
            />
            <section className="rounded-lg bg-paper p-4 shadow-panel">
              <div className="flex items-center gap-2 text-sm font-semibold text-moss">
                <CheckCircle2 size={18} />
                <span>最近练习</span>
              </div>
              <div className="mt-3 space-y-3">
                {history.length === 0 ? (
                  <p className="text-sm text-moss">完成第一句后，这里会显示练习记录。</p>
                ) : (
                  history.slice(0, 5).map((item) => (
                    <div key={item.id} className="rounded-md border border-ink/10 bg-white p-3">
                      <div className="flex items-center justify-between gap-3">
                        <p className="line-clamp-1 text-sm font-semibold">{item.user_input}</p>
                        <span className="rounded-full bg-leaf/10 px-2 py-1 text-xs font-bold text-leaf">{item.score}</span>
                      </div>
                      <p className="mt-1 line-clamp-1 text-xs text-moss">{item.feedback.corrected_sentence}</p>
                    </div>
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
