import { Check, RefreshCw } from "lucide-react"

export function ReviewQueue({ items, onMarkMastered, onRefresh }) {
  return (
    <section className="rounded-lg bg-paper p-4 shadow-panel">
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-2 text-sm font-semibold text-moss">
          <RefreshCw size={18} />
          <span>复习队列</span>
        </div>
        <button
          type="button"
          onClick={onRefresh}
          className="h-8 rounded-md border border-ink/10 bg-white px-3 text-xs font-bold text-moss"
        >
          刷新
        </button>
      </div>

      <div className="mt-3 space-y-3">
        {items.length === 0 ? (
          <p className="rounded-md bg-white p-3 text-sm leading-6 text-moss">
            暂时没有到期复习。低分句子会在第二天回到这里。
          </p>
        ) : (
          items.map((item) => (
            <article key={item.attempt_id} className="rounded-md border border-ink/10 bg-white p-3">
              <p className="text-sm font-bold leading-6">{item.cn_sentence}</p>
              <p className="mt-2 text-xs text-moss">你的回答：{item.user_input}</p>
              <p className="mt-1 text-xs text-moss">推荐表达：{item.corrected_sentence}</p>
              <div className="mt-3 flex items-center justify-between gap-3">
                <span className="rounded-full bg-coral/10 px-2 py-1 text-xs font-bold text-coral">
                  Score {item.score}
                </span>
                <button
                  type="button"
                  onClick={() => onMarkMastered(item.attempt_id)}
                  className="inline-flex h-8 items-center rounded-md bg-leaf px-3 text-xs font-bold text-white"
                >
                  <Check className="mr-1" size={14} />
                  已掌握
                </button>
              </div>
            </article>
          ))
        )}
      </div>
    </section>
  )
}
