import { getServerClient } from "@/lib/supabase"
import { Post, PostStatus } from "@/lib/types"
import { PostCard } from "@/components/PostCard"

export const dynamic = "force-dynamic"

async function fetchStats(client: ReturnType<typeof getServerClient>) {
  const [pending, approved, published] = await Promise.all([
    client.from("posts").select("id", { count: "exact", head: true }).eq("status", PostStatus.PENDING),
    client.from("posts").select("id", { count: "exact", head: true }).eq("status", PostStatus.APPROVED),
    client.from("posts").select("id", { count: "exact", head: true }).eq("status", PostStatus.PUBLISHED),
  ])
  return {
    pending: pending.count ?? 0,
    approved: approved.count ?? 0,
    published: published.count ?? 0,
  }
}

export default async function PostsPage() {
  let posts: Post[] = []
  let stats = { pending: 0, approved: 0, published: 0 }
  let configError: string | null = null

  try {
    const client = getServerClient()
    const [{ data }, fetchedStats] = await Promise.all([
      client
        .from("posts")
        .select("*")
        .in("status", [PostStatus.PENDING, PostStatus.APPROVED])
        .order("created_at", { ascending: false }),
      fetchStats(client),
    ])
    posts = (data ?? []) as Post[]
    stats = fetchedStats
  } catch (err) {
    configError = err instanceof Error ? err.message : "Failed to connect to database"
  }

  if (configError) {
    return (
      <div className="flex flex-col items-center justify-center h-64 text-center">
        <p className="text-red-400 font-semibold mb-2">Configuration error</p>
        <p className="text-sm text-gray-500 max-w-md">{configError}</p>
        <p className="text-xs text-gray-600 mt-4">
          Set NEXT_PUBLIC_SUPABASE_URL, NEXT_PUBLIC_SUPABASE_ANON_KEY, and SUPABASE_SERVICE_ROLE_KEY in Vercel → Settings → Environment Variables, then redeploy.
        </p>
      </div>
    )
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-bold text-white">Post Queue</h1>
        <div className="flex gap-4 text-sm text-gray-400">
          <span><span className="text-yellow-400 font-semibold">{stats.pending}</span> pending</span>
          <span><span className="text-emerald-400 font-semibold">{stats.approved}</span> approved</span>
          <span><span className="text-purple-400 font-semibold">{stats.published}</span> published</span>
        </div>
      </div>

      {posts.length === 0 ? (
        <div className="flex flex-col items-center justify-center h-64 text-gray-600">
          <p className="text-lg">No posts to review</p>
          <p className="text-sm mt-1">Run the pipeline to generate new content</p>
        </div>
      ) : (
        <>
          {posts.some(p => p.status === PostStatus.PENDING) && (
            <div className="mb-2">
              <p className="text-xs text-yellow-400 font-semibold uppercase tracking-widest mb-3">Pending review</p>
              <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4">
                {posts.filter(p => p.status === PostStatus.PENDING).map(post => (
                  <PostCard key={post.id} post={post} />
                ))}
              </div>
            </div>
          )}
          {posts.some(p => p.status === PostStatus.APPROVED) && (
            <div className={posts.some(p => p.status === PostStatus.PENDING) ? "mt-8" : ""}>
              <p className="text-xs text-emerald-400 font-semibold uppercase tracking-widest mb-3">Approved — awaiting schedule</p>
              <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4">
                {posts.filter(p => p.status === PostStatus.APPROVED).map(post => (
                  <PostCard key={post.id} post={post} />
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  )
}
