import { getServerClient } from "@/lib/supabase"
import { Post, PostStatus } from "@/lib/types"
import { PostCard } from "@/components/PostCard"
import Link from "next/link"

export const dynamic = "force-dynamic"

const TAB_CONFIG = [
  { key: "pending",   label: "Pending",   color: "yellow"  },
  { key: "approved",  label: "Approved",  color: "emerald" },
  { key: "published", label: "Published", color: "purple"  },
  { key: "rejected",  label: "Rejected",  color: "red"     },
] as const

type TabKey = typeof TAB_CONFIG[number]["key"]

const TAB_ACTIVE: Record<string, string> = {
  yellow:  "border-yellow-400 text-yellow-400",
  emerald: "border-emerald-400 text-emerald-400",
  purple:  "border-purple-400 text-purple-400",
  red:     "border-red-400 text-red-400",
}

const TAB_BADGE: Record<string, string> = {
  yellow:  "bg-yellow-400/15 text-yellow-400",
  emerald: "bg-emerald-400/15 text-emerald-400",
  purple:  "bg-purple-400/15 text-purple-400",
  red:     "bg-red-400/15 text-red-400",
}

export default async function PostsPage({
  searchParams,
}: {
  searchParams: Promise<{ tab?: string }>
}) {
  const { tab: rawTab } = await searchParams
  const activeTab: TabKey = (TAB_CONFIG.find(t => t.key === rawTab)?.key ?? "pending") as TabKey

  let configError: string | null = null
  let posts: Post[] = []
  let counts: Record<string, number> = {}

  try {
    const client = getServerClient()

    const [{ data }, ...countResults] = await Promise.all([
      client
        .from("posts")
        .select("*")
        .eq("status", activeTab)
        .order("created_at", { ascending: false }),
      ...TAB_CONFIG.map(t =>
        client.from("posts").select("id", { count: "exact", head: true }).eq("status", t.key)
      ),
    ])

    posts = (data ?? []) as Post[]
    TAB_CONFIG.forEach((t, i) => {
      counts[t.key] = countResults[i].count ?? 0
    })
  } catch (err) {
    configError = err instanceof Error ? err.message : "Failed to connect to database"
  }

  if (configError) {
    return (
      <div className="p-8 flex flex-col items-center justify-center h-64 text-center">
        <p className="text-red-400 font-semibold mb-2">Configuration error</p>
        <p className="text-sm text-gray-500 max-w-md">{configError}</p>
        <p className="text-xs text-gray-600 mt-4">
          Set NEXT_PUBLIC_SUPABASE_URL, NEXT_PUBLIC_SUPABASE_ANON_KEY, and SUPABASE_SERVICE_ROLE_KEY in Vercel → Settings → Environment Variables, then redeploy.
        </p>
      </div>
    )
  }

  const total = Object.values(counts).reduce((a, b) => a + b, 0)

  return (
    <div className="p-8">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-white">Posts</h1>
        <p className="text-sm text-gray-500 mt-1">{total} total across all statuses</p>
      </div>

      {/* Tab bar */}
      <div className="flex gap-0 border-b border-white/8 mb-6 -mx-1">
        {TAB_CONFIG.map(({ key, label, color }) => {
          const isActive = key === activeTab
          const count = counts[key] ?? 0
          return (
            <Link
              key={key}
              href={`/posts?tab=${key}`}
              className={`relative px-4 py-2.5 text-sm font-medium transition-colors border-b-2 -mb-px mx-1 ${
                isActive
                  ? `${TAB_ACTIVE[color]} bg-transparent`
                  : "border-transparent text-gray-500 hover:text-gray-300"
              }`}
            >
              {label}
              {count > 0 && (
                <span className={`ml-2 text-xs px-1.5 py-0.5 rounded-full font-semibold ${
                  isActive ? TAB_BADGE[color] : "bg-white/6 text-gray-500"
                }`}>
                  {count}
                </span>
              )}
            </Link>
          )
        })}
      </div>

      {/* Grid */}
      {posts.length === 0 ? (
        <div className="flex flex-col items-center justify-center h-56 text-gray-600 border border-white/5 rounded-xl">
          <p className="text-base">No {activeTab} posts</p>
          <p className="text-sm mt-1 text-gray-700">
            {activeTab === "pending"
              ? "Run the pipeline to generate new content"
              : `No posts with status "${activeTab}" yet`}
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4">
          {posts.map(post => (
            <PostCard key={post.id} post={post} />
          ))}
        </div>
      )}
    </div>
  )
}
