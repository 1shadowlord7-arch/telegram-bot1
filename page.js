'use client'

import { useState } from 'react'
import BottomNav from '@/components/navigation/BottomNav'
import HomeScreen from '@/components/screens/HomeScreen'
import GamesScreen from '@/components/screens/GamesScreen'
import MissionsScreen from '@/components/screens/MissionsScreen'
import FriendsScreen from '@/components/screens/FriendsScreen'
import WalletScreen from '@/components/screens/WalletScreen'
import ProfileScreen from '@/components/screens/ProfileScreen'

const App = () => {
  const [tab, setTab] = useState('home')

  const render = () => {
    switch (tab) {
      case 'home':
        return <HomeScreen onNavigate={setTab} />
      case 'games':
        return <GamesScreen />
      case 'missions':
        return <MissionsScreen />
      case 'friends':
        return <FriendsScreen />
      case 'wallet':
        return <WalletScreen />
      case 'profile':
        return <ProfileScreen />
      default:
        return <HomeScreen onNavigate={setTab} />
    }
  }

  const navTab = tab === 'wallet' ? 'home' : tab

  return (
    <main className="relative h-[100dvh] w-full max-w-[480px] mx-auto bg-background overflow-hidden">
      <div className="pointer-events-none absolute inset-0 -z-0">
        <div className="absolute -top-24 -left-24 h-72 w-72 rounded-full bg-primary/10 blur-3xl" />
        <div className="absolute -bottom-32 -right-24 h-80 w-80 rounded-full bg-accent/10 blur-3xl" />
      </div>
      <div
        key={tab}
        className="relative h-full z-10 animate-in fade-in slide-in-from-bottom-1 duration-300"
      >
        {render()}
      </div>
      <BottomNav active={navTab} onChange={setTab} />
    </main>
  )
}

export default App
