'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import type { ReactNode } from 'react'

const NAV_ITEMS = [
  { href: '/', label: 'Overview' },
  { href: '/agents', label: 'Agents' },
  { href: '/journeys', label: 'Journeys' },
  { href: '/concierge', label: 'Concierge' },
  { href: '/properties', label: 'Properties' },
]

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname()

  return (
    <main className="app-shell">
      <section className="shell-top">
        <h1>EnterpriseHub Client Showcase</h1>
        <p>Operational dashboard with API-backed pages and built-in demo fallback mode.</p>
        <nav className="nav-grid" aria-label="Primary">
          {NAV_ITEMS.map((item) => {
            const active = pathname === item.href
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`nav-pill${active ? ' active' : ''}`}
              >
                {item.label}
              </Link>
            )
          })}
        </nav>
      </section>
      <div className="page-container">{children}</div>
    </main>
  )
}
