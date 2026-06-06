import type { Metadata } from "next"
import Link from "next/link"
import "./globals.css"

export const metadata: Metadata = {
  title: "EduBot Dashboard",
  description: "Review and schedule automated education posts",
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="h-full dark">
      <body className="h-full flex bg-gray-950 text-gray-100">
        <aside className="w-52 shrink-0 border-r border-gray-800 flex flex-col pt-6 px-4 gap-1">
          <span className="text-xs font-bold text-gray-500 uppercase tracking-widest px-2 mb-3">
            EduBot
          </span>
          <NavLink href="/posts">Post Queue</NavLink>
          <NavLink href="/schedule">Schedule</NavLink>
        </aside>
        <main className="flex-1 overflow-y-auto p-8">{children}</main>
      </body>
    </html>
  )
}

function NavLink({ href, children }: { href: string; children: React.ReactNode }) {
  return (
    <Link
      href={href}
      className="px-3 py-2 rounded text-sm text-gray-400 hover:text-white hover:bg-gray-800 transition-colors"
    >
      {children}
    </Link>
  )
}
