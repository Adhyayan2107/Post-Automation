import { NextResponse } from "next/server"

const OWNER    = process.env.GITHUB_OWNER
const REPO     = process.env.GITHUB_REPO
const TOKEN    = process.env.GITHUB_PAT
const WORKFLOW = "dashboard_run.yml"

function ghFetch(path: string, options?: RequestInit) {
  return fetch(`https://api.github.com${path}`, {
    ...options,
    headers: {
      Authorization: `Bearer ${TOKEN}`,
      Accept: "application/vnd.github+json",
      "X-GitHub-Api-Version": "2022-11-28",
      "Content-Type": "application/json",
      ...options?.headers,
    },
  })
}

function sleep(ms: number) {
  return new Promise(r => setTimeout(r, ms))
}

export async function POST() {
  if (!OWNER || !REPO || !TOKEN) {
    return NextResponse.json(
      { error: "Missing env vars: GITHUB_PAT, GITHUB_OWNER, GITHUB_REPO" },
      { status: 500 }
    )
  }

  const dispatchedAt = Date.now()

  const dispatchResp = await ghFetch(
    `/repos/${OWNER}/${REPO}/actions/workflows/${WORKFLOW}/dispatches`,
    { method: "POST", body: JSON.stringify({ ref: "main" }) }
  )

  if (!dispatchResp.ok) {
    const text = await dispatchResp.text()
    return NextResponse.json({ error: `Dispatch failed (${dispatchResp.status}): ${text}` }, { status: 500 })
  }

  // Poll until the new run appears (max ~40s)
  for (let i = 0; i < 10; i++) {
    await sleep(4000)
    const runsResp = await ghFetch(
      `/repos/${OWNER}/${REPO}/actions/workflows/${WORKFLOW}/runs?per_page=5`
    )
    if (!runsResp.ok) continue

    const { workflow_runs } = await runsResp.json() as {
      workflow_runs: { id: number; html_url: string; created_at: string }[]
    }

    const run = workflow_runs.find(
      r => new Date(r.created_at).getTime() >= dispatchedAt - 5000
    )

    if (run) {
      return NextResponse.json({ runId: run.id, runUrl: run.html_url })
    }
  }

  return NextResponse.json({ error: "Timed out waiting for run to start" }, { status: 504 })
}
