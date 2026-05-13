import { Badge } from '@/components/ui/badge'
import { Gamepad2 } from 'lucide-react'

export default function GameCard({ game }) {
  return (
    <div className="group relative overflow-hidden rounded-2xl border border-border bg-card grad-border">
      <div className={`relative aspect-[4/3] bg-gradient-to-br ${game.accent}`}>
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_30%_20%,rgba(255,255,255,0.12),transparent_50%)]" />
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="h-12 w-12 rounded-2xl bg-black/40 backdrop-blur flex items-center justify-center border border-white/10">
            <Gamepad2 className="h-6 w-6 text-white/80" />
          </div>
        </div>
        <Badge className="absolute top-2 right-2 bg-black/55 text-white border border-white/10 hover:bg-black/55 text-[10px] font-medium">
          Coming Soon
        </Badge>
      </div>

      <div className="p-3">
        <p className="text-sm font-medium leading-tight truncate">{game.title}</p>
        <p className="text-[11px] text-muted-foreground mt-0.5">{game.category}</p>
      </div>
    </div>
  )
}
