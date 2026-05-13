export default function SectionHeader({ title, action }) {
  return (
    <div className="flex items-center justify-between mb-3 px-1">
      <h2 className="text-base font-semibold tracking-tight">{title}</h2>
      {action ? (
        <div className="text-xs text-muted-foreground">{action}</div>
      ) : null}
    </div>
  )
}
