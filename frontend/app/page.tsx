"use client";
import { useEffect } from "react";
import { MenuButton } from "@/components/MenuButton";
import { Card } from "@/components/Card";

const botUsername = process.env.NEXT_PUBLIC_BOT_USERNAME || "your_bot_username";

const buttons = [
  { label: "➕ Add to Group", route: `https://t.me/${botUsername}?startgroup=true` },
  { label: "⚙️ Group Settings", route: "/group-settings" },
  { label: "🕹 Play Games", route: "/games" },
  { label: "👥 Friends", route: "/friends" },
  { label: "📂 Linked Files", route: "/files" },
  { label: "🛒 Market", route: "/market" },
  { label: "👑 Owner", route: "/owner" },
  { label: "📢 Join Updates Channel", route: "/updates" },
];

export default function Home() {
  useEffect(() => {
    // @ts-expect-error Telegram injected object
    window.Telegram?.WebApp?.ready?.();
    // @ts-expect-error Telegram injected object
    window.Telegram?.WebApp?.expand?.();
  }, []);

  return (
    <main className="min-h-screen bg-gradient-to-b from-slate-950 via-slate-900 to-slate-950 p-4">
      <div className="mx-auto max-w-md space-y-4">
        <Card title="Premium Bot" subtitle="Modern, modular, Telegram-native mini app.">
          <div className="grid grid-cols-1 gap-3">
            {buttons.map((b) => (
              <a key={b.label} href={b.route} className="block">
                <MenuButton label={b.label} />
              </a>
            ))}
          </div>
        </Card>
      </div>
    </main>
  );
}
