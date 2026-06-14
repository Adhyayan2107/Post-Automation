"use client"

import { useState, useTransition } from "react"
import { approvePost, rejectPost, editPost } from "@/actions/posts"
import { Post, PostStatus } from "@/lib/types"

export function ApprovalButtons({ post }: { post: Post }) {
  const [isPending, startTransition] = useTransition()
  const [title, setTitle] = useState(post.title)
  const [body, setBody] = useState(post.body)

  const isRejected  = post.status === PostStatus.REJECTED
  const isPublished = post.status === PostStatus.PUBLISHED

  const titleChanged = title !== post.title
  const bodyChanged  = body  !== post.body
  const hasChanges   = titleChanged || bodyChanged

  function handleApprove() {
    startTransition(async () => {
      if (hasChanges) await editPost(post.id, title, body)
      await approvePost(post.id)
    })
  }

  function handleReject() {
    startTransition(async () => { await rejectPost(post.id) })
  }

  function handleSaveOnly() {
    startTransition(async () => { await editPost(post.id, title, body) })
  }

  if (isPublished) {
    return <p className="text-xs text-gray-600">This post has been published and cannot be changed.</p>
  }

  return (
    <div className="flex flex-col gap-4">
      {/* Always-visible editable fields */}
      <div className="flex flex-col gap-3">
        <div>
          <label className="block text-xs text-gray-500 mb-1.5 font-medium uppercase tracking-widest">
            Title
            {titleChanged && <span className="ml-2 text-amber-400 normal-case tracking-normal font-normal">edited</span>}
          </label>
          <input
            value={title}
            onChange={e => setTitle(e.target.value)}
            disabled={isPublished}
            className="w-full bg-white/4 border border-white/8 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-emerald-500/50 transition-colors disabled:opacity-50"
          />
        </div>
        <div>
          <label className="block text-xs text-gray-500 mb-1.5 font-medium uppercase tracking-widest">
            Body
            {bodyChanged && <span className="ml-2 text-amber-400 normal-case tracking-normal font-normal">edited</span>}
          </label>
          <textarea
            value={body}
            onChange={e => setBody(e.target.value)}
            disabled={isPublished}
            rows={14}
            className="w-full bg-white/4 border border-white/8 rounded-lg px-3 py-2 text-sm text-white font-mono focus:outline-none focus:border-emerald-500/50 transition-colors resize-y disabled:opacity-50"
          />
        </div>
      </div>

      {/* Save edits without approving */}
      {hasChanges && !isRejected && (
        <button
          onClick={handleSaveOnly}
          disabled={isPending}
          className="self-start text-xs text-amber-400 hover:text-amber-300 underline transition-colors disabled:opacity-40"
        >
          {isPending ? "Saving…" : "Save edits only (keep current status)"}
        </button>
      )}

      {/* Approve / Reject */}
      <div className="flex gap-3">
        <button
          onClick={handleApprove}
          disabled={isPending}
          className="flex-1 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-40 disabled:cursor-not-allowed text-white font-semibold text-sm py-2.5 rounded-lg transition-colors"
        >
          {isPending
            ? "Saving…"
            : isRejected
            ? "Un-reject (Approve)"
            : hasChanges
            ? "Save & Approve"
            : "Approve"}
        </button>
        {!isRejected && (
          <button
            onClick={handleReject}
            disabled={isPending}
            className="flex-1 bg-white/5 hover:bg-red-500/20 hover:text-red-400 disabled:opacity-40 disabled:cursor-not-allowed text-gray-300 font-semibold text-sm py-2.5 rounded-lg transition-colors border border-white/8 hover:border-red-500/30"
          >
            {isPending ? "Saving…" : "Reject"}
          </button>
        )}
      </div>

      {isRejected && (
        <p className="text-xs text-gray-700">Rejected. Click approve above to restore it.</p>
      )}
    </div>
  )
}
