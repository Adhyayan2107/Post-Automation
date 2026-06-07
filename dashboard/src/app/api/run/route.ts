import { spawn } from "child_process"
import path from "path"

export const runtime = "nodejs"

export async function POST() {
  const projectRoot = path.resolve(process.cwd(), "..")
  const encoder = new TextEncoder()

  const stream = new ReadableStream({
    start(controller) {
      const send = (payload: object) => {
        try {
          controller.enqueue(
            encoder.encode(`data: ${JSON.stringify(payload)}\n\n`)
          )
        } catch {
          // controller already closed
        }
      }

      const proc = spawn("uv", ["run", "python", "scripts/mini_run.py"], {
        cwd: projectRoot,
        env: { ...process.env },
      })

      proc.stdout.on("data", (chunk: Buffer) => {
        for (const line of chunk.toString().split("\n")) {
          if (line.trim()) send({ line, stream: "stdout" })
        }
      })

      proc.stderr.on("data", (chunk: Buffer) => {
        for (const line of chunk.toString().split("\n")) {
          if (line.trim()) send({ line, stream: "stderr" })
        }
      })

      proc.on("error", (err: Error) => {
        send({ line: `Failed to start process: ${err.message}`, stream: "error" })
        send({ done: true, code: 1 })
        controller.close()
      })

      proc.on("close", (code: number | null) => {
        send({ done: true, code: code ?? 1 })
        controller.close()
      })
    },
  })

  return new Response(stream, {
    headers: {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache",
      Connection: "keep-alive",
    },
  })
}
