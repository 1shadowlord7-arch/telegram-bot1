"use client";
import { motion } from "framer-motion";
import type { ReactNode } from "react";
import clsx from "clsx";

export function Card({ title, subtitle, children, className }: { title: string; subtitle?: string; children?: ReactNode; className?: string }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className={clsx("rounded-3xl border border-white/10 bg-white/8 p-5 shadow-soft backdrop-blur", className)}
    >
      <div className="mb-3">
        <h2 className="text-xl font-semibold">{title}</h2>
        {subtitle ? <p className="mt-1 text-sm text-white/70">{subtitle}</p> : null}
      </div>
      {children}
    </motion.div>
  );
}
