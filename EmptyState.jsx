import { Sparkles } from 'lucide-react'

export default function EmptyState({
  icon: Icon = Sparkles,
  title = 'Nothing here yet',
  subtitle = 'Check back soon.',
}) {
  return (
    <div className="flex flex-col items-center justify-center text-center py-10 px-6 rounded-2xl border border-dashed border-border bg-card/40">
      <div className="h-12 w-12 rounded-full grad-primary flex items-center justify-center mb-3">
        <Icon className="h-5 w-5 text-primary-foreground" />
      </div>
      <p className="font-medium">{title}</p>
      <p className="text-sm text-muted-foreground mt-1">{subtitle}</p>
    </div>
  )
}
