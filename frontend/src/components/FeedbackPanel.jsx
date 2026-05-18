import { Sparkles } from "lucide-react"

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

export function FeedbackPanel({ feedback, hints }) {
  return (
    <section className="rounded-lg bg-paper p-4 shadow-panel sm:p-5">
      <div className="flex items-center gap-2 text-sm font-semibold text-moss">
        <Sparkles size={18} />
        <span>AI 点评</span>
      </div>

      {!feedback ? (
        <div className="mt-4 rounded-lg border border-dashed border-ink/20 bg-white p-5 text-sm leading-6 text-moss">
          提交你的英文表达后，这里会显示分数、修改建议和更自然的表达版本。
        </div>
      ) : (
        <div className="mt-4 space-y-4">
          <div className="rounded-lg bg-ink p-4 text-white">
            <p className="text-sm font-semibold text-white/70">Score</p>
            <p className="mt-1 text-5xl font-black">{feedback.score}</p>
          </div>

          <div className="space-y-3 rounded-lg border border-ink/10 bg-white p-4">
            <ScoreBar label="Grammar" value={feedback.grammar_score} />
            <ScoreBar label="Authenticity" value={feedback.authenticity_score} />
            <ScoreBar label="Politeness" value={feedback.politeness_score} />
          </div>

          <div className="rounded-lg border border-ink/10 bg-white p-4">
            <p className="text-xs font-bold uppercase text-coral">Better sentence</p>
            <p className="mt-2 text-lg font-bold leading-7">{feedback.corrected_sentence}</p>
            <p className="mt-3 text-sm leading-6 text-moss">{feedback.feedback_cn}</p>
          </div>

          {feedback.mistakes.length > 0 ? (
            <div className="rounded-lg border border-ink/10 bg-white p-4">
              <p className="text-sm font-bold text-moss">需要注意</p>
              <div className="mt-3 space-y-3">
                {feedback.mistakes.map((mistake, index) => (
                  <div key={`${mistake.type}-${index}`} className="rounded-md bg-skyglass p-3">
                    <p className="text-sm font-bold">{mistake.suggestion}</p>
                    <p className="mt-1 text-xs leading-5 text-moss">{mistake.explanation_cn}</p>
                  </div>
                ))}
              </div>
            </div>
          ) : null}
        </div>
      )}

      {hints ? (
        <div className="mt-4 rounded-lg border border-coral/30 bg-coral/10 p-4">
          <p className="text-sm font-bold text-coral">表达提示</p>
          <div className="mt-3 space-y-2 text-sm leading-6">
            <p><strong>Polite:</strong> {hints.hints.polite}</p>
            <p><strong>Neutral:</strong> {hints.hints.neutral}</p>
            <p><strong>Casual:</strong> {hints.hints.casual}</p>
          </div>
          <p className="mt-3 text-sm leading-6 text-moss">{hints.explanation_cn}</p>
        </div>
      ) : null}
    </section>
  )
}
