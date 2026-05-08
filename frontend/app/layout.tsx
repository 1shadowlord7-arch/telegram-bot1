import "./globals.css";
import type { ReactNode } from "react";

export const metadata = {
  title: "Premium Telegram Bot",
  description: "Telegram Mini App",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
