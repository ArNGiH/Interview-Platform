import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "Intervue | AI Interview Platform",
  description: "A SaaS interview workspace for resume-aware technical interviews."
};

export default function RootLayout({
  children
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>
        <div className="app-shell">
          <header className="topbar">
            <div className="topbar-inner">
              <Link className="brand" href="/">
                <span className="brand-mark">I</span>
                <span className="brand-title">
                  <strong>Intervue</strong>
                  <span>AI interview workspace</span>
                </span>
              </Link>

              <nav className="nav-actions" aria-label="Primary navigation">
                <Link className="button button-ghost" href="/">
                  Home
                </Link>
                <Link className="button button-ghost" href="/interviews">
                  Interviews
                </Link>
                <Link className="button button-secondary" href="/setup">
                  New interview
                </Link>
              </nav>
            </div>
          </header>

          {children}
        </div>
      </body>
    </html>
  );
}
