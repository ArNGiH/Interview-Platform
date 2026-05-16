"use client";

import Link from "next/link";
import { FormEvent, useEffect, useMemo, useRef, useState } from "react";
import { useParams } from "next/navigation";
import { sendInterviewMessage } from "@/lib/api";
import type { InterviewMessage } from "@/types/api";
import type { StoredInterviewSession } from "@/types/session";

function fallbackSession(interviewId: string): StoredInterviewSession {
  return {
    interviewId,
    role: "Interview session",
    experienceLevel: "Configured",
    difficulty: "Active",
    interviewType: "Interview",
    interviewMode: "Live chat",
    resumeName: "",
    firstQuestion: "This interview is ready. Send your response to continue.",
    startedAt: new Date().toISOString()
  };
}

export default function InterviewChatPage() {
  const params = useParams<{ interviewId: string }>();
  const interviewId = params.interviewId;
  const [session, setSession] = useState<StoredInterviewSession>(() =>
    fallbackSession(interviewId)
  );
  const [messages, setMessages] = useState<InterviewMessage[]>([]);
  const [draft, setDraft] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState("");
  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const stored = sessionStorage.getItem(`interview:${interviewId}`);
    const parsedSession = stored
      ? (JSON.parse(stored) as StoredInterviewSession)
      : fallbackSession(interviewId);

    setSession(parsedSession);
    setMessages([
      {
        id: `${interviewId}:assistant:initial`,
        role: "assistant",
        content: parsedSession.firstQuestion,
        createdAt: parsedSession.startedAt
      }
    ]);
  }, [interviewId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({
      behavior: "smooth"
    });
  }, [messages]);

  const answeredCount = useMemo(() => {
    return messages.filter((message) => message.role === "user").length;
  }, [messages]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const trimmedDraft = draft.trim();

    if (!trimmedDraft || isSending) {
      return;
    }

    setError("");
    setDraft("");
    setIsSending(true);

    const candidateMessage: InterviewMessage = {
      id: `${interviewId}:user:${Date.now()}`,
      role: "user",
      content: trimmedDraft,
      createdAt: new Date().toISOString()
    };

    setMessages((currentMessages) => [...currentMessages, candidateMessage]);

    try {
      const response = await sendInterviewMessage({
        interview_id: interviewId,
        message: trimmedDraft
      });

      const assistantMessage: InterviewMessage = {
        id: `${interviewId}:assistant:${Date.now()}`,
        role: "assistant",
        content: response.question,
        createdAt: new Date().toISOString()
      };

      setMessages((currentMessages) => [...currentMessages, assistantMessage]);
    } catch (chatError) {
      setError(chatError instanceof Error ? chatError.message : "Message failed");
      setDraft(trimmedDraft);
    } finally {
      setIsSending(false);
    }
  }

  return (
    <main className="chat-page">
      <div className="chat-shell">
        <aside className="chat-sidebar">
          <div className="sidebar-block">
            <h2>{session.role}</h2>
            <p>
              Interview ID
              <br />
              {interviewId}
            </p>
          </div>

          <div className="sidebar-block">
            <h3>Round controls</h3>
            <div className="chip-row">
              <span className="chip">{session.difficulty}</span>
              <span className="chip">{session.interviewType}</span>
              <span className="chip">{session.interviewMode.replace("_", " ")}</span>
            </div>
          </div>

          <div className="sidebar-block">
            <h3>Progress</h3>
            <p>{answeredCount} candidate answer{answeredCount === 1 ? "" : "s"} submitted.</p>
          </div>

          <div className="sidebar-block">
            <h3>Resume</h3>
            <p>{session.resumeName || "No resume attached to this browser session."}</p>
          </div>

          <div className="sidebar-block">
            <Link className="button button-secondary" href="/setup">
              New interview
            </Link>
          </div>
        </aside>

        <section className="chat-main">
          <header className="chat-header">
            <div>
              <h1>Live interview</h1>
              <p>Answer naturally. The next question is generated from your last response.</p>
            </div>

            <span className="status-pill">
              <span className="status-dot status-dot-online" />
              Session active
            </span>
          </header>

          <div className="messages" aria-live="polite">
            {messages.map((message) => (
              <article className={`message ${message.role}`} key={message.id}>
                <div className="message-meta">
                  {message.role === "assistant" ? "Interviewer" : "Candidate"}
                </div>
                <div className="bubble">{message.content}</div>
              </article>
            ))}

            {isSending ? (
              <article className="message assistant">
                <div className="message-meta">Interviewer</div>
                <div className="bubble">Reviewing your answer and preparing the next question...</div>
              </article>
            ) : null}

            <div ref={messagesEndRef} />
          </div>

          <div className="composer">
            {error ? <div className="error-box">{error}</div> : null}

            <form className="composer-form" onSubmit={handleSubmit}>
              <textarea
                aria-label="Candidate answer"
                value={draft}
                onChange={(event) => setDraft(event.target.value)}
                placeholder="Type your answer as the candidate..."
              />

              <button className="button button-primary" type="submit" disabled={isSending || !draft.trim()}>
                {isSending ? "Sending..." : "Send answer"}
              </button>
            </form>
          </div>
        </section>
      </div>
    </main>
  );
}
