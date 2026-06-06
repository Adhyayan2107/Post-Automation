import { PostStatus } from "@/lib/types"
import { cn } from "@/lib/utils"

const colours: Record<PostStatus, string> = {
  [PostStatus.PENDING]:   "bg-yellow-500/20 text-yellow-400 border-yellow-500/30",
  [PostStatus.APPROVED]:  "bg-emerald-500/20 text-emerald-400 border-emerald-500/30",
  [PostStatus.REJECTED]:  "bg-red-500/20 text-red-400 border-red-500/30",
  [PostStatus.SCHEDULED]: "bg-blue-500/20 text-blue-400 border-blue-500/30",
  [PostStatus.PUBLISHED]: "bg-purple-500/20 text-purple-400 border-purple-500/30",
  [PostStatus.FAILED]:    "bg-gray-500/20 text-gray-400 border-gray-500/30",
}

export function StatusBadge({ status }: { status: PostStatus }) {
  return (
    <span className={cn(
      "inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border",
      colours[status]
    )}>
      {status}
    </span>
  )
}
