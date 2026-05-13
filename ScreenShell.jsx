export default function ScreenShell({ children, title, right }) {
  return (
    <div className="flex flex-col h-full">
      {title ? (
        <div className="sticky top-0 z-20 glass safe-top">
          <div className="px-5 pt-4 pb-3 flex items-center justify-between">
            <h1 className="text-xl font-semibold tracking-tight">{title}</h1>
            {right}
          </div>
          <div className="h-px bg-gradient-to-r from-transparent via-border to-transparent" />
        </div>
      ) : null}
      <div className="flex-1 overflow-y-auto no-scrollbar pb-28">
        <div className="px-4 pt-4 space-y-5">{children}</div>
      </div>
    </div>
  )
}
