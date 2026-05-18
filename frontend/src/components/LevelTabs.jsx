const levels = [
  { value: 1, label: "启蒙" },
  { value: 2, label: "进阶" },
  { value: 3, label: "实战" },
]

export function LevelTabs({ value, onChange }) {
  return (
    <div className="grid h-11 grid-cols-3 rounded-lg border border-ink/10 bg-white p-1">
      {levels.map((level) => (
        <button
          key={level.value}
          type="button"
          onClick={() => onChange(level.value)}
          className={`rounded-md px-4 text-sm font-bold transition ${
            value === level.value ? "bg-ink text-white" : "text-moss hover:bg-skyglass"
          }`}
        >
          {level.label}
        </button>
      ))}
    </div>
  )
}
