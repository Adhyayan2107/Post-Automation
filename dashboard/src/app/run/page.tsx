"use client"

import { useState, useRef, useEffect } from "react"
import { Play, Terminal, CheckCircle2, XCircle, Loader2 } from "lucide-react"

type LogLine = {
  text: string
  stream: "stdout" | "stderr" | "error" | "info"
}

type RunState = "idle" | "running" | "done" | "failed"

export default function RunPage() {
  const [state, setState] = useState<RunState>("idle")
  const [exitCode, setExitCode] = useState<number | null>(null)
  const [lines, setLines] = useState<LogLine[]>([])
  const bottomRef = useRef<HTMLDivElement>(null)
  const abortRef = useRef<AbortController | null>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [lines])

  async function handleRun() {
    if (state === "running") return

    setState("running")
    setExitCode(null)
    setLines([{ text: "▶  Starting mini_run.py…", stream: "info" }])

    abortRef.current = new AbortController()

    let resp: Response
    try {
      resp = await fetch("/api/run", {
        method: "POST",
        signal: abortRef.current.signal,
      })
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
      } catch {
        break
      }
      if (result.done) break

      buf += decoder.decode(result.value, { stream: true })
      const parts = buf.split("\n\n")
      buf = parts.pop() ?? ""

      for (const part of parts) {
        const dataLine = part.split("\n").find(l => l.startsWith("data: "))
        if (!dataLine) continue
        let payload: { line?: string; stream?: string; done?: boolean; code?: number }
        try {
          payload = JSON.parse(dataLine.slice(6))
        } catch {
          continue
        }
        if (payload.done) {
          const code = payload.code ?? 1
          setExitCode(code)
          setState(code === 0 ? "done" : "failed")
          setLines(l => [
            ...l,
            {
              text: code === 0 ? "✓  Run completed successfully." : `✗  Run exited with code ${code}.`,
              stream: code === 0 ? "info" : "error",
            },
          ])
        } else if (payload.line) {
          setLines(l => [
            ...l,
            { text: payload.line!, stream: (payload.stream as LogLine["stream"]) ?? "stdout" },
          ])
        }
      }
    }

    setState(s => (s === "running" ? "failed" : s))
  }

  const statusBadge = () => {
    if (state === "running")
      return (
        <span className="flex items-center gap-1.5 text-xs text-blue-400">
          <Loader2 className="w-3 h-3 animate-spin" /> Running…
        </span>
      )
    if (state === "done")
      return (
        <span className="flex items-center gap-1.5 text-xs text-emerald-400">
          <CheckCircle2 className="w-3 h-3" /> Completed
        </span>
      )
    if (state === "failed")
      return (
        <span className="flex items-center gap-1.5 text-xs text-red-400">
          <XCircle className="w-3 h-3" /> Failed {exitCode !== null ? `(exit ${exitCode})` : ""}
        </span>
      )
    return null
  }

  return (
    <div className="p-8 h-full flex flex-col">
      {/* Header */}
      <div className="mb-6 flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Run Pipeline</h1>
          <p className="text-sm text-gray-500 mt-1">
            Scrape → Generate → Images → Save → Auto-approve → Schedule
          </p>
        </div>
        <button
          onClick={handleRun}
          disabled={state === "running"}
          className="flex items-center gap-2 px-5 py-2.5 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-40 disabled:cursor-not-allowed text-white font-semibold text-sm rounded-lg transition-colors"
        >
          {state === "running" ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <Play className="w-4 h-4" />
          )}
          {state === "running" ? "Running…" : "Run Now"}
        </button>
      </div>

      {/* Info cards */}
      <div className="grid grid-cols-3 gap-3 mb-6">
        {[
          { label: "Scrape", desc: "IB news + RSS feeds (7-day cache)" },
          { label: "Generate", desc: "2 edu + 2 creative posts via Claude" },
          { label: "Schedule", desc: "Slots on Google Calendar" },
        ].map(({ label, desc }) => (
          <div key={label} className="bg-white/3 border border-white/6 rounded-xl px-4 py-3">
            <p className="text-xs font-semibold text-gray-400">{label}</p>
            <p className="text-[11px] text-gray-600 mt-0.5">{desc}</p>
          </div>
        ))}
      </div>

      {/* Terminal output */}
      {lines.length > 0 && (
        <div className="flex-1 flex flex-col bg-[#06060c] border border-white/8 rounded-xl overflow-hidden min-h-0">
          <div className="flex items-center gap-2 px-4 py-2.5 border-b border-white/8 bg-white/2 shrink-0">
            <Terminal className="w-3.5 h-3.5 text-gray-600" />
            <span className="text-xs text-gray-600 font-mono">mini_run.py</span>
            <div className="ml-auto">{statusBadge()}</div>
          </div>

          <div className="flex-1 overflow-y-auto p-4 font-mono text-xs leading-6">
            {lines.map((l, i) => (
              <div
                key={i}
                className={
                  l.stream === "stderr"
                    ? "text-yellow-400/80"
                    : l.stream === "error"
                    ? "text-red-400"
                    : l.stream === "info"
                    ? "text-gray-500"
                    : "text-gray-300"
                }
              >
                {l.text}
              </div>
            ))}
            <div ref={bottomRef} />
          </div>
        </div>
      )}

      {/* Idle placeholder */}
      {lines.length === 0 && (
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <Terminal className="w-10 h-10 text-gray-800 mx-auto mb-3" />
            <p className="text-sm text-gray-600">Output will appear here when the run starts.</p>
          </div>
        </div>
      )}
    </div>
  )
}
