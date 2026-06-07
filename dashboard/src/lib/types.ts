export enum PostStatus {
  PENDING = "pending",
  APPROVED = "approved",
  REJECTED = "rejected",
  SCHEDULED = "scheduled",
  PUBLISHED = "published",
  FAILED = "failed",
}

export interface Post {
  id: string
  title: string
  body: string
  post_type: "educational" | "creative"
  creative_angle: "anime" | "movie" | "history" | null
  image_url: string | null
  source_urls: string[]
  target_platforms: string[]
  target_subreddits: string[]
  status: PostStatus
  scheduled_at: string | null
  gcal_event_id: string | null
  published_at: string | null
  created_at: string
  run_id: string
}
