import { getServerClient } from "@/lib/supabase"
import { Post, PostStatus } from "@/lib/types"
import { PostCard } from "@/components/PostCard"

export const dynamic = "force-dynamic"

async function fetchStats(client: ReturnType<typeof getServerClient>) {
  const [pending, approved, scheduled, published, rejected] = await Promise.all([
    client.from("posts").select("id", { count: "exact", head: true }).eq("status", PostStatus.PENDING),
    client.from("posts").select("id", { count: "exact", head: true }).eq("status", PostStatus.APPROVED),
    client.from("posts").select("id", { count: "exact", head: true }).eq("status", PostStatus.SCHEDULED),
    client.from("posts").select("id", { count: "exact", head: true }).eq("status", PostStatus.PUBLISHED),
    client.from("posts").select("id", { count: "exact", head: true }).eq("status", PostStatus.REJECTED),
  ])
  return {
    pending: pending.count ?? 0,
    approved: approved.count ?? 0,
    scheduled: scheduled.count ?? 0,
    published: published.count ?? 0,
    rejected: rejected.count ?? 0,
  }
}

function Section({
  label,
  labelColor,
  posts,
}: {
  label: string
  labelColor: string
  posts: Post[]
}) {
  if (posts.length === 0) return null
  return (
    <div className="mb-8">
      <p className={`text-xs font-semibold uppercase tracking-widest mb-3 ${labelColor}`}>
        {label} ({posts.length})
      </p>
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4">
        {posts.map(post => (
          <PostCard key={post.id} post={post} />
        ))}
      </div>
    </div>
  )
}

export default async function PostsPage() {
  let posts: Post[] = []
  let stats = { pending: 0, approved: 0, scheduled: 0, published: 0, rejected: 0 }
  let configError: string | null = null

  try {
    const client = getServerClient()
    const [{ data }, fetchedStats] = await Promise.all([
      client
        .from("posts")
        .select("*")
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

  const byStatus = (status: PostStatus) => posts.filter(p => p.status === status)

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-bold text-white">All Posts</h1>
        <div className="flex gap-3 text-sm text-gray-400 flex-wrap justify-end">
          {stats.pending > 0 && <span><span className="text-yellow-400 font-semibold">{stats.pending}</span> pending</span>}
          {stats.approved > 0 && <span><span className="text-emerald-400 font-semibold">{stats.approved}</span> approved</span>}
          {stats.scheduled > 0 && <span><span className="text-blue-400 font-semibold">{stats.scheduled}</span> scheduled</span>}
          {stats.published > 0 && <span><span className="text-purple-400 font-semibold">{stats.published}</span> published</span>}
          {stats.rejected > 0 && <span><span className="text-red-400 font-semibold">{stats.rejected}</span> rejected</span>}
        </div>
      </div>

      {posts.length === 0 ? (
        <div className="flex flex-col items-center justify-center h-64 text-gray-600">
          <p className="text-lg">No posts yet</p>
          <p className="text-sm mt-1">Run the pipeline to generate new content</p>
        </div>
      ) : (
        <>
          <Section label="Pending review" labelColor="text-yellow-400" posts={byStatus(PostStatus.PENDING)} />
          <Section label="Approved — awaiting schedule" labelColor="text-emerald-400" posts={byStatus(PostStatus.APPROVED)} />
          <Section label="Scheduled" labelColor="text-blue-400" posts={byStatus(PostStatus.SCHEDULED)} />
          <Section label="Published" labelColor="text-purple-400" posts={byStatus(PostStatus.PUBLISHED)} />
          <Section label="Rejected" labelColor="text-red-400" posts={byStatus(PostStatus.REJECTED)} />
        </>
      )}
    </div>
  )
}
