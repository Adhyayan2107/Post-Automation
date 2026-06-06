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
  const client = getServerClient()

  const [{ data }, stats] = await Promise.all([
    client.from("posts").select("*").eq("status", PostStatus.PENDING).order("created_at", { ascending: false }),
    fetchStats(client),
  ])

  const posts = (data ?? []) as Post[]

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
          <p className="text-lg">No pending posts</p>
          <p className="text-sm mt-1">Run the pipeline to generate new content</p>
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
