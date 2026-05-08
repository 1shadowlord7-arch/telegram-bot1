"use client";
import { motion } from "framer-motion";

export function MenuButton({ label, onClick, href }: { label: string; onClick?: () => void; href?: string }) {
  const Comp: any = motion.button;
  return (
    <Comp
      whileTap={{ scale: 0.98 }}
      whileHover={{ y: -1 }}
      className="w-full rounded-3xl bg-white/10 px-4 py-4 text-left text-base font-medium shadow-soft backdrop-blur border border-white/10"
      onClick={onClick}
    >
      {label}
    </Comp>
  );
}
