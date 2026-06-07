"use server"

import { revalidatePath } from "next/cache"
import { redirect } from "next/navigation"
import { getServiceClient } from "@/lib/supabase"

export async function approvePost(id: string): Promise<void> {
  const client = getServiceClient()
  const { error } = await client
    .from("posts")
    .update({ status: "approved" })
    .eq("id", id)

  if (error) throw new Error(`Failed to approve post: ${error.message}`)

  revalidatePath("/posts")
  redirect("/posts")
}

export async function rejectPost(id: string): Promise<void> {
  const client = getServiceClient()
  const { error } = await client
    .from("posts")
    .update({ status: "rejected" })
    .eq("id", id)

  if (error) throw new Error(`Failed to reject post: ${error.message}`)

  revalidatePath("/posts")
  redirect("/posts")
}

export async function reschedulePost(id: string, scheduledAt: string): Promise<void> {
  const client = getServiceClient()
  const { error } = await client
    .from("posts")
    .update({ scheduled_at: scheduledAt })
    .eq("id", id)

  if (error) throw new Error(`Failed to reschedule post: ${error.message}`)

  revalidatePath("/schedule")
}

export async function editPost(
  id: string,
  title: string,
  body: string
): Promise<void> {
  const client = getServiceClient()
  const { error } = await client
    .from("posts")
    .update({ title, body })
    .eq("id", id)

  if (error) throw new Error(`Failed to edit post: ${error.message}`)

  revalidatePath(`/posts/${id}`)
}
