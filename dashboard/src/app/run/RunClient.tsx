"use client"

import { useState, useRef, useEffect, useCallback } from "react"
import {
  Play,
  Terminal,
  CheckCircle2,
  XCircle,
  Loader2,
  Database,
  DollarSign,
  Layers,
  Clock,
  AlertTriangle,
} from "lucide-react"
import { formatDistanceToNow, parseISO } from "date-fns"

export type CacheStatus = {
  hasCache: boolean
  count: number
  lastScrapedAt: string | null
}

type LogLine = {
  text: string
  stream: "stdout" | "stderr" | "error" | "info"
}

type RunState = "idle" | "running" | "done" | "failed"

const STEPS = [
  { key: "scrape",   label: "Scrape sources",      detail: "IB news + RSS feeds",           scrapedOnly: true  },
  { key: "generate", label: "Generate 4 posts",     detail: "2 edu + 2 creative via Claude",  scrapedOnly: false },
  { key: "images",   label: "Source images",        detail: "Pexels · Jikan · TMDb",          scrapedOnly: false },
  { key: "save",     label: "Save to Supabase",     detail: "All 4 posts",                    scrapedOnly: false },
  { key: "approve",  label: "Auto-approve",         detail: "Mark approved",                  scrapedOnly: false },
  { key: "schedule", label: "Schedule",             detail: "Google Calendar slots",          scrapedOnly: false },
]

function CostBadge({ hasCache }: { hasCache: boolean }) {
  return hasCache ? (
    <span className="text-emerald-400 font-bold">~$0.10 – $0.12</span>
  ) : (
    <span className="text-amber-400 font-bold">~$0.25 – $0.30</span>
  )
}

export function RunClient({ initialCache }: { initialCache: CacheStatus }) {
  const [cache, setCache] = useState(initialCache)
  const [state, setState] = useState<RunState>("idle")
  const [exitCode, setExitCode] = useState<number | null>(null)
  const [lines, setLines] = useState<LogLine[]>([])
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [lines])

  const refreshCache = useCallback(async () => {
    try {
      const resp = await fetch("/api/run-status")
      if (resp.ok) setCache(await resp.json())
    } catch { /* network error, ignore */ }
  }, [])

  async function handleRun() {
    if (state === "running") return

    setState("running")
    setExitCode(null)
    setLines([{ text: "▶  Starting mini_run.py…", stream: "info" }])

    let resp: Response
    try {
      resp = await fetch("/api/run", { method: "POST" })
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err)
      setLines(l => [...l, { text: `Connection error: ${msg}`, stream: "error" }])
      setState("failed")
      return
    }

    if (!resp.ok) {
      const text = await resp.text()
      setLines(l => [...l, { text: text, stream: "error" }])
      setState("failed")
      return
    }

    const reader = resp.body!.getReader()
    const decoder = new TextDecoder()
    let buf = ""

    while (true) {
      let result: ReadableStreamReadResult<Uint8Array>
      try {
        result = await reader.read()
      } catch { break }
      if (result.done) break

      buf += decoder.decode(result.value, { stream: true })
      const parts = buf.split("\n\n")
      buf = parts.pop() ?? ""

      for (const part of parts) {
        const dataLine = part.split("\n").find(l => l.startsWith("data: "))
        if (!dataLine) continue
        let payload: { line?: string; stream?: string; done?: boolean; code?: number }
        try { payload = JSON.parse(dataLine.slice(6)) } catch { continue }

        if (payload.done) {
          const code = payload.code ?? 1
          setExitCode(code)
          setState(code === 0 ? "done" : "failed")
          setLines(l => [...l, {
            text: code === 0 ? "✓  Completed successfully." : `✗  Exited with code ${code}.`,
            stream: code === 0 ? "info" : "error",
          }])
          refreshCache()
        } else if (payload.line) {
          setLines(l => [...l, {
            text: payload.line!,
            stream: (payload.stream as LogLine["stream"]) ?? "stdout",
          }])
        }
      }
    }

    setState(s => s === "running" ? "failed" : s)
  }

  const cacheAge = cache.lastScrapedAt
    ? formatDistanceToNow(parseISO(cache.lastScrapedAt), { addSuffix: true })
    : null

  const estimateLow  = cache.hasCache ? "$0.10" : "$0.25"
  const estimateHigh = cache.hasCache ? "$0.12" : "$0.30"

  return (
    <div className="p-8 flex flex-col gap-6 min-h-full">

      {/* ── Header ── */}
      <div className="flex items-start justify-between gap-6">
        <div>
          <h1 className="text-2xl font-bold text-white">Run Pipeline</h1>
          <p className="text-sm text-gray-500 mt-1">
            Scrape → Generate → Images → Save → Auto-approve → Schedule
          </p>
        </div>

        <div className="flex flex-col items-end gap-1.5 shrink-0">
          <button
            onClick={handleRun}
            disabled={state === "running"}
            className="flex items-center gap-2.5 px-5 py-2.5 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-40 disabled:cursor-not-allowed text-white font-semibold text-sm rounded-xl transition-colors shadow-lg shadow-emerald-900/30"
          >
            {state === "running"
              ? <Loader2 className="w-4 h-4 animate-spin" />
              : <Play className="w-4 h-4" />
            }
            {state === "running" ? "Running…" : "Run Now"}
          </button>
          <span className="text-[11px] text-gray-600">
            est. <CostBadge hasCache={cache.hasCache} /> per run
          </span>
        </div>
      </div>

      {/* ── Status cards ── */}
      <div className="grid grid-cols-3 gap-4">

        {/* Cache card */}
        <div className={`rounded-2xl border p-5 flex flex-col gap-3 ${
          cache.hasCache
            ? "bg-emerald-950/20 border-emerald-900/40"
            : "bg-amber-950/15 border-amber-900/30"
        }`}>
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-semibold text-gray-500 uppercase tracking-widest">Raw Content</span>
            <Database className={`w-3.5 h-3.5 ${cache.hasCache ? "text-emerald-500" : "text-amber-500"}`} />
          </div>
          {cache.hasCache ? (
            <>
              <div>
                <p className="text-2xl font-bold text-white">{cache.count}</p>
                <p className="text-xs text-gray-500 mt-0.5">cached items</p>
              </div>
              <div className="flex items-center gap-1.5">
                <Clock className="w-3 h-3 text-emerald-600" />
                <span className="text-[11px] text-emerald-600">Scraped {cacheAge}</span>
              </div>
              <div className="flex items-center gap-1.5 bg-emerald-500/10 border border-emerald-500/20 rounded-lg px-3 py-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                <span className="text-xs text-emerald-400 font-medium">Cache hit — scraping skipped</span>
              </div>
            </>
          ) : (
            <>
              <div>
                <p className="text-2xl font-bold text-white">0</p>
                <p className="text-xs text-gray-500 mt-0.5">recent items</p>
              </div>
              <div className="flex items-center gap-1.5">
                <AlertTriangle className="w-3 h-3 text-amber-600" />
                <span className="text-[11px] text-amber-600">No recent cache found</span>
              </div>
              <div className="flex items-center gap-1.5 bg-amber-500/10 border border-amber-500/20 rounded-lg px-3 py-2">
                <Loader2 className="w-3.5 h-3.5 text-amber-400 shrink-0" />
                <span className="text-xs text-amber-400 font-medium">Will scrape all sources</span>
              </div>
            </>
          )}
        </div>

        {/* Cost card */}
        <div className="rounded-2xl border border-white/8 bg-white/3 p-5 flex flex-col gap-3">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-semibold text-gray-500 uppercase tracking-widest">Est. Cost</span>
            <DollarSign className="w-3.5 h-3.5 text-gray-600" />
          </div>
          <div>
            <p className={`text-2xl font-bold ${cache.hasCache ? "text-emerald-400" : "text-amber-400"}`}>
              {estimateLow} – {estimateHigh}
            </p>
            <p className="text-xs text-gray-500 mt-0.5">Claude API tokens</p>
          </div>
          <div className="flex flex-col gap-1.5 mt-auto">
            <div className="flex items-center justify-between text-[11px]">
              <span className="text-gray-600">Scraping</span>
              <span className={cache.hasCache ? "text-emerald-600" : "text-amber-400"}>
                {cache.hasCache ? "SKIP" : "~$0.12–0.15"}
              </span>
            </div>
            <div className="flex items-center justify-between text-[11px]">
              <span className="text-gray-600">Generation (4 posts)</span>
              <span className="text-gray-400">~$0.10–0.12</span>
            </div>
            <div className="flex items-center justify-between text-[11px]">
              <span className="text-gray-600">Images</span>
              <span className="text-emerald-600">Free</span>
            </div>
          </div>
        </div>

        {/* Steps card */}
        <div className="rounded-2xl border border-white/8 bg-white/3 p-5 flex flex-col gap-3">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-semibold text-gray-500 uppercase tracking-widest">Pipeline Steps</span>
            <Layers className="w-3.5 h-3.5 text-gray-600" />
          </div>
          <div className="flex flex-col gap-2 mt-1">
            {STEPS.map(step => {
              const skipped = step.scrapedOnly && cache.hasCache
              return (
                <div key={step.key} className="flex items-center gap-2.5">
                  {skipped ? (
                    <span className="w-4 h-4 rounded-full bg-white/5 border border-white/10 flex items-center justify-center shrink-0">
                      <span className="w-1 h-1 rounded-full bg-gray-700" />
                    </span>
                  ) : (
                    <span className="w-4 h-4 rounded-full bg-emerald-500/15 border border-emerald-500/25 flex items-center justify-center shrink-0">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                    </span>
                  )}
                  <div className="flex-1 min-w-0">
                    <p className={`text-[11px] font-medium leading-none ${skipped ? "text-gray-700 line-through" : "text-gray-300"}`}>
                      {step.label}
                    </p>
                    <p className={`text-[10px] mt-0.5 ${skipped ? "text-gray-800" : "text-gray-600"}`}>
                      {skipped ? "cache hit" : step.detail}
                    </p>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      </div>

      {/* ── Terminal ── */}
      <div className={`flex flex-col rounded-2xl border overflow-hidden transition-all ${
        lines.length > 0
          ? "border-white/8 flex-1 min-h-[320px]"
          : "border-white/4 border-dashed"
      }`}>
        {lines.length > 0 ? (
          <>
            {/* Terminal bar */}
            <div className="flex items-center gap-2 px-4 py-2.5 border-b border-white/8 bg-white/2 shrink-0">
              <div className="flex gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-red-500/50" />
                <span className="w-2.5 h-2.5 rounded-full bg-yellow-500/50" />
                <span className="w-2.5 h-2.5 rounded-full bg-emerald-500/50" />
              </div>
              <Terminal className="w-3 h-3 text-gray-600 ml-1" />
              <span className="text-xs text-gray-600 font-mono">mini_run.py</span>

              <div className="ml-auto flex items-center gap-2">
                {state === "running" && (
                  <span className="flex items-center gap-1.5 text-[11px] text-blue-400 font-medium">
                    <Loader2 className="w-3 h-3 animate-spin" /> Running
                  </span>
                )}
                {state === "done" && (
                  <span className="flex items-center gap-1.5 text-[11px] text-emerald-400 font-medium">
                    <CheckCircle2 className="w-3 h-3" /> Completed
                  </span>
                )}
                {state === "failed" && (
                  <span className="flex items-center gap-1.5 text-[11px] text-red-400 font-medium">
                    <XCircle className="w-3 h-3" /> Failed {exitCode !== null ? `(exit ${exitCode})` : ""}
                  </span>
                )}
              </div>
            </div>

            {/* Log output */}
            <div className="flex-1 overflow-y-auto p-4 font-mono text-[11px] leading-[1.75] bg-[#060609]">
              {lines.map((l, i) => (
                <div key={i} className={
                  l.stream === "stderr" ? "text-yellow-400/80" :
                  l.stream === "error"  ? "text-red-400"       :
                  l.stream === "info"   ? "text-gray-600 italic" :
                  "text-gray-300"
                }>
                  {l.text}
                </div>
              ))}
              <div ref={bottomRef} />
            </div>
          </>
        ) : (
          /* Idle placeholder */
          <div className="flex flex-col items-center justify-center gap-3 py-12">
            <Terminal className="w-8 h-8 text-gray-800" />
            <p className="text-sm text-gray-700">Terminal output will appear here when the run starts.</p>
          </div>
        )}
      </div>
    </div>
  )
}
