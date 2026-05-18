export function KeywordCard({ keyword }) {
  return (
    <div className="min-h-32 rounded-lg border border-ink/10 bg-white p-4">
      <div className="flex min-h-12 flex-col justify-between">
        <p className="text-lg font-bold text-ink">{keyword.text}</p>
        {keyword.phonetic ? <p className="text-xs font-semibold text-coral">{keyword.phonetic}</p> : null}
      </div>
      <p className="mt-3 text-sm font-semibold text-moss">{keyword.meaning_cn}</p>
      {keyword.example ? <p className="mt-2 text-xs leading-5 text-moss/80">{keyword.example}</p> : null}
    </div>
  )
}
