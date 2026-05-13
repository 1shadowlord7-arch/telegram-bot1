'use client'

import { Home, Gamepad2, Target, Users, User } from 'lucide-react'
import { cn } from '@/lib/utils'

const tabs = [
  { id: 'home', label: 'Home', icon: Home },
  { id: 'games', label: 'Games', icon: Gamepad2 },
  { id: 'missions', label: 'Missions', icon: Target },
  { id: 'friends', label: 'Friends', icon: Users },
  { id: 'profile', label: 'Profile', icon: User },
]

export default function BottomNav({ active, onChange }) {
  return (
    <nav className="absolute bottom-0 inset-x-0 z-30 safe-bottom">
      <div className="mx-3 mb-3 rounded-2xl border border-border glass shadow-2xl shadow-black/40">
        <div className="grid grid-cols-5">
          {tabs.map((t) => {
            const Icon = t.icon
            const isActive = active === t.id

            return (
              <button
                key={t.id}
                onClick={() => onChange(t.id)}
                className="relative flex flex-col items-center justify-center py-2.5 group"
              >
                {isActive ? (
                  <span className="absolute top-0 h-0.5 w-8 rounded-b-full grad-primary" />
                ) : null}
                <Icon
                  className={cn(
                    'h-5 w-5 transition-colors',
                    isActive
                      ? 'text-primary'
                      : 'text-muted-foreground group-active:text-foreground'
                  )}
                />
                <span
                  className={cn(
                    'mt-1 text-[10px] font-medium transition-colors',
                    isActive ? 'text-foreground' : 'text-muted-foreground'
                  )}
                >
                  {t.label}
                </span>
              </button>
            )
          })}
        </div>
      </div>
    </nav>
  )
}
