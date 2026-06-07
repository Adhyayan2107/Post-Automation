import { NextResponse } from "next/server"

const OWNER = process.env.GITHUB_OWNER
const REPO  = process.env.GITHUB_REPO
const TOKEN = process.env.GITHUB_PAT

export const dynamic = "force-dynamic"

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url)
  const runId = searchParams.get("runId")

  if (!runId)  return NextResponse.json({ error: "Missing runId" }, { status: 400 })
  if (!TOKEN)  return NextResponse.json({ error: "GITHUB_PAT not set" }, { status: 500 })

  const resp = await fetch(
    `https://api.github.com/repos/${OWNER}/${REPO}/actions/runs/${runId}/jobs`,
    {
      headers: {
        Authorization: `Bearer ${TOKEN}`,
        Accept: "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
      },
    }
  )

  if (!resp.ok) {
    return NextResponse.json({ error: "GitHub API error" }, { status: resp.status })
  }

  const { jobs } = await resp.json() as {
    jobs: {
      status: string
      conclusion: string | null
      steps: { name: string; status: string; conclusion: string | null; number: number }[]
    }[]
  }

  const job = jobs?.[0]
  if (!job) return NextResponse.json({ status: "queued", steps: [] })

  return NextResponse.json({
    status:     job.status,
    conclusion: job.conclusion,
    steps:      job.steps ?? [],
  })
}
