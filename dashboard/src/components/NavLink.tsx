"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"

export function NavLink({ href, children }: { href: string; children: React.ReactNode }) {
  const pathname = usePathname()
  const isActive = pathname === href || pathname.startsWith(href + "/")

  return (
    <Link
      href={href}
      className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-colors ${
        isActive
          ? "bg-white/8 text-white font-medium"
          : "text-gray-400 hover:text-gray-200 hover:bg-white/4"
      }`}
    >
      {children}
    </Link>
  )
}
