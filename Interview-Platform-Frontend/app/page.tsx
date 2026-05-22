import Link from "next/link";
import { HomeHealth } from "@/components/HomeHealth";

export default function HomePage() {
  return (
    <main className="page">
      <section className="hero-grid">
        <div>
          <p className="eyebrow">Resume-aware technical interviews</p>
          <h1 className="hero-title">Run sharper interviews without losing the human signal.</h1>
          <p className="hero-copy">
            Upload a resume, configure the round, and conduct an AI-guided interview that adapts
            to the candidate&apos;s answers, role, difficulty, and project background.
          </p>

          <div className="hero-actions">
            <Link className="button button-primary" href="/setup">
              Create interview
            </Link>
            <HomeHealth />
          </div>

          <div className="metrics-row" aria-label="Product highlights">
            <div className="metric">
              <strong>4</strong>
              <span>Backend workflows integrated</span>
            </div>
            <div className="metric">
              <strong>RAG</strong>
              <span>Resume-grounded follow-ups</span>
            </div>
            <div className="metric">
              <strong>Live</strong>
              <span>Structured interview chat</span>
            </div>
          </div>
        </div>

        <div className="interview-visual" aria-label="Interview workspace preview">
          <div className="visual-top">
            <strong>Frontend Developer Round</strong>
            <div className="visual-dots" aria-hidden="true">
              <span />
              <span />
              <span />
            </div>
          </div>

          <div className="visual-body">
            <aside className="visual-sidebar">
              <div className="visual-nav-item active" />
              <div className="visual-nav-item" />
              <div className="visual-nav-item" />
              <div className="visual-nav-item" />
            </aside>

            <div className="visual-main">
              <div className="screen-row">
                <div className="screen-tile">
                  <div className="screen-avatar" />
                  <div className="screen-line" />
                  <div className="screen-line short" />
                </div>
                <div className="screen-tile">
                  <div className="screen-avatar" />
                  <div className="screen-line" />
                  <div className="screen-line short" />
                </div>
              </div>

              <div className="transcript-panel">
                <div className="transcript-line">
                  <span className="transcript-speaker">AI</span>
                  <span className="transcript-text" />
                </div>
                <div className="transcript-line">
                  <span className="transcript-speaker">Candidate</span>
                  <span className="transcript-text" />
                </div>
                <div className="transcript-line">
                  <span className="transcript-speaker">Strategy</span>
                  <span className="transcript-text" />
                </div>
                <div className="transcript-line">
                  <span className="transcript-speaker">Next</span>
                  <span className="transcript-text" />
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>
    </main>
  );
}
