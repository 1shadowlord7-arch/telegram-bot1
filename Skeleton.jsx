export function SkelLine({ className = '' }) {
  return <div className={`shimmer rounded-md bg-secondary/60 ${className}`} />
}

export function SkelCard({ className = '' }) {
  return (
    <div
      className={`shimmer rounded-2xl bg-secondary/40 border border-border ${className}`}
    />
  )
}
