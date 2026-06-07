import type { Metadata } from "next"
import "./globals.css"
import { NavLink } from "@/components/NavLink"

export const metadata: Metadata = {
  title: "EduBot",
  description: "Review and schedule automated education posts",
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="h-full">
      <body className="h-full flex bg-[#0a0a0f] text-gray-100 antialiased">
        <aside className="w-56 shrink-0 border-r border-white/5 flex flex-col">
          {/* Logo */}
          <div className="px-5 pt-6 pb-4 border-b border-white/5">
            <div className="flex items-center gap-2">
              <div className="w-7 h-7 rounded-lg bg-emerald-500/20 flex items-center justify-center">
                <span className="text-emerald-400 text-sm font-bold">E</span>
              </div>
              <span className="font-semibold text-white text-sm tracking-tight">EduBot</span>
            </div>
          </div>

          {/* Nav */}
          <nav className="flex-1 px-3 py-4 flex flex-col gap-1">
            <p className="text-[10px] font-semibold text-gray-600 uppercase tracking-widest px-2 mb-2">Content</p>
            <NavLink href="/posts">Posts</NavLink>
            <NavLink href="/schedule">Schedule</NavLink>
            <div className="my-2 border-t border-white/5" />
            <p className="text-[10px] font-semibold text-gray-600 uppercase tracking-widest px-2 mb-2">Pipeline</p>
            <NavLink href="/run">Run</NavLink>
          </nav>
        </aside>

        <main className="flex-1 overflow-y-auto">{children}</main>
      </body>
    </html>
  )
}
