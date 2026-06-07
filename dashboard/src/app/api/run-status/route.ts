import { getServerClient } from "@/lib/supabase"
import { NextResponse } from "next/server"

export const dynamic = "force-dynamic"

export async function GET() {
  try {
    const client = getServerClient()
    const sevenDaysAgo = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString()

    const { data, count } = await client
      .from("raw_content")
      .select("scraped_at", { count: "exact" })
      .gte("scraped_at", sevenDaysAgo)
      .order("scraped_at", { ascending: false })
      .limit(1)

    const hasCache = (count ?? 0) > 0
    const lastScrapedAt = data?.[0]?.scraped_at ?? null

    return NextResponse.json({ hasCache, count: count ?? 0, lastScrapedAt })
  } catch {
    return NextResponse.json({ hasCache: false, count: 0, lastScrapedAt: null })
  }
}
