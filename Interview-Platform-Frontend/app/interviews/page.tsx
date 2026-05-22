"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { getInterviewSessions } from "@/utils/api/chat";
import { getApiErrorMessage } from "@/utils/api/client";
import type { InterviewSessionSummary, InterviewStatus } from "@/types/api";

function formatDate(value: string | null) {
  if (!value) {
    return "Not started";
  }

  return new Intl.DateTimeFormat("en", {
    dateStyle: "medium",
    timeStyle: "short"
  }).format(new Date(value));
}

function formatLabel(value: string) {
  return value.replaceAll("_", " ");
}

function formatStatus(value: InterviewStatus) {
  return value.charAt(0).toUpperCase() + value.slice(1);
}

export default function InterviewsPage() {
  const [sessions, setSessions] = useState<InterviewSessionSummary[]>([]);
  const [selectedStatus, setSelectedStatus] = useState<InterviewStatus | "all">("all");
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let isMounted = true;

    async function loadSessions() {
      setIsLoading(true);
      setError("");

      try {
        const response = await getInterviewSessions();

        if (isMounted) {
          setSessions(response.sessions);
        }
      } catch (loadError) {
        if (isMounted) {
          setError(getApiErrorMessage(loadError, "Could not load interviews"));
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    }

    loadSessions();

    return () => {
      isMounted = false;
    };
  }, []);

  const filteredSessions = useMemo(() => {
    if (selectedStatus === "all") {
      return sessions;
    }

    return sessions.filter((session) => session.status === selectedStatus);
  }, [selectedStatus, sessions]);

  const activeCount = sessions.filter((session) => session.status === "active").length;
  const submittedCount = sessions.filter((session) => session.status === "submitted").length;

  return (
    <main className="page">
      <div className="section-header">
        <div>
          <p className="eyebrow">Interview history</p>
          <h1>Resume previous interviews or review submitted rounds.</h1>
          <p>
            Active interviews reopen the live chat with full history. Submitted interviews open a
            placeholder review screen until feedback is added later.
          </p>
        </div>

        <Link className="button button-primary" href="/setup">
          New interview
        </Link>
      </div>

      <section className="history-toolbar" aria-label="Interview filters">
        <button
          className={`filter-button ${selectedStatus === "all" ? "active" : ""}`}
          type="button"
          onClick={() => setSelectedStatus("all")}
        >
          All
          <span>{sessions.length}</span>
        </button>
        <button
          className={`filter-button ${selectedStatus === "active" ? "active" : ""}`}
          type="button"
          onClick={() => setSelectedStatus("active")}
        >
          Active
          <span>{activeCount}</span>
        </button>
        <button
          className={`filter-button ${selectedStatus === "submitted" ? "active" : ""}`}
          type="button"
          onClick={() => setSelectedStatus("submitted")}
        >
          Submitted
          <span>{submittedCount}</span>
        </button>
      </section>

      {error ? <div className="error-box">{error}</div> : null}

      <section className="history-list" aria-live="polite">
        {isLoading ? (
          <div className="empty-state">
            <h2>Loading interviews</h2>
            <p>Fetching your active and submitted sessions.</p>
          </div>
        ) : null}

        {!isLoading && filteredSessions.length === 0 ? (
          <div className="empty-state">
            <h2>No interviews found</h2>
            <p>Create a new interview, then it will appear here as active.</p>
            <Link className="button button-primary" href="/setup">
              Create interview
            </Link>
          </div>
        ) : null}

        {!isLoading
          ? filteredSessions.map((session) => {
              const href =
                session.status === "active"
                  ? `/interview/${session.interview_id}`
                  : `/interview/${session.interview_id}/submitted`;

              return (
                <Link className="history-row" href={href} key={session.interview_id}>
                  <div className="history-row-main">
                    <div>
                      <h2>{session.role}</h2>
                      <p>
                        {formatLabel(session.interview_type)} · {formatLabel(session.interview_mode)}
                      </p>
                    </div>

                    <span className={`status-pill status-${session.status}`}>
                      <span
                        className={`status-dot ${
                          session.status === "active" ? "status-dot-online" : ""
                        }`}
                      />
                      {formatStatus(session.status)}
                    </span>
                  </div>

                  <div className="history-meta">
                    <span>{session.experience_level}</span>
                    <span>{session.difficulty}</span>
                    <span>{session.message_count} messages</span>
                    <span>Last activity: {formatDate(session.last_message_at || session.created_at)}</span>
                  </div>
                </Link>
              );
            })
          : null}
      </section>
    </main>
  );
}
