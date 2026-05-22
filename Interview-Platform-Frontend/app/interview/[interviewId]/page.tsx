"use client";

import Link from "next/link";
import { FormEvent, useEffect, useMemo, useRef, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import {
  getInterviewHistory,
  sendInterviewMessage,
  submitInterview
} from "@/utils/api/chat";
import { getApiErrorMessage } from "@/utils/api/client";
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
    startedAt: new Date().toISOString(),
    status: "active"
  };
}

function formatStatus(value: StoredInterviewSession["status"]) {
  if (!value) {
    return "Active";
  }

  return value.charAt(0).toUpperCase() + value.slice(1);
}

export default function InterviewChatPage() {
  const params = useParams<{ interviewId: string }>();
  const router = useRouter();
  const interviewId = params.interviewId;
  const [session, setSession] = useState<StoredInterviewSession>(() =>
    fallbackSession(interviewId)
  );
  const [messages, setMessages] = useState<InterviewMessage[]>([]);
  const [draft, setDraft] = useState("");
  const [isLoadingHistory, setIsLoadingHistory] = useState(true);
  const [isSending, setIsSending] = useState(false);
  const [isEnding, setIsEnding] = useState(false);
  const [error, setError] = useState("");
  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    let isMounted = true;

    async function loadHistory() {
      setIsLoadingHistory(true);
      setError("");

      try {
        const response = await getInterviewHistory(interviewId);

        if (!isMounted) {
          return;
        }

        if (response.session.status === "submitted") {
          router.replace(`/interview/${interviewId}/submitted`);
          return;
        }

        const firstAssistantMessage = response.messages.find(
          (message) => message.role === "assistant"
        );

        setSession({
          interviewId: response.session.interview_id,
          role: response.session.role,
          experienceLevel: response.session.experience_level,
          difficulty: response.session.difficulty,
          interviewType: response.session.interview_type,
          interviewMode: response.session.interview_mode,
          resumeName: response.session.resume_uploaded ? "Resume attached" : "",
          firstQuestion:
            firstAssistantMessage?.content ||
            "This interview is ready. Send your response to continue.",
          startedAt: response.session.created_at || new Date().toISOString(),
          status: response.session.status
        });

        setMessages(
          response.messages.map((message) => ({
            id: message.id,
            role: message.role,
            content: message.content,
            createdAt: message.created_at || new Date().toISOString()
          }))
        );
      } catch (historyError) {
        if (!isMounted) {
          return;
        }

        setSession(fallbackSession(interviewId));
        setMessages([]);
        setError(getApiErrorMessage(historyError, "Could not load interview history"));
      } finally {
        if (isMounted) {
          setIsLoadingHistory(false);
        }
      }
    }

    loadHistory();

    return () => {
      isMounted = false;
    };
  }, [interviewId, router]);

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

    if (!trimmedDraft || isSending || isLoadingHistory) {
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
      setError(getApiErrorMessage(chatError, "Message failed"));
      setDraft(trimmedDraft);
    } finally {
      setIsSending(false);
    }
  }

  async function handleEndInterview() {
    if (isEnding || isSending || isLoadingHistory) {
      return;
    }

    setError("");
    setIsEnding(true);

    try {
      await submitInterview(interviewId);
      router.push(`/interview/${interviewId}/submitted`);
    } catch (submitError) {
      setError(getApiErrorMessage(submitError, "Could not end interview"));
    } finally {
      setIsEnding(false);
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
            <div className="sidebar-actions">
              <Link className="button button-secondary" href="/setup">
                New interview
              </Link>
              <Link className="button button-ghost" href="/interviews">
                Previous interviews
              </Link>
            </div>
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
              {formatStatus(session.status)}
            </span>
            <button
              className="button button-secondary"
              type="button"
              onClick={handleEndInterview}
              disabled={isLoadingHistory || isSending || isEnding}
            >
              {isEnding ? "Ending..." : "End interview"}
            </button>
          </header>

          <div className="messages" aria-live="polite">
            {isLoadingHistory ? (
              <article className="message assistant">
                <div className="message-meta">Interviewer</div>
                <div className="bubble">Loading interview history...</div>
              </article>
            ) : null}

            {!isLoadingHistory && messages.length === 0 ? (
              <article className="message assistant">
                <div className="message-meta">Interviewer</div>
                <div className="bubble">{session.firstQuestion}</div>
              </article>
            ) : null}

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
                disabled={isLoadingHistory}
              />

              <button
                className="button button-primary"
                type="submit"
                disabled={isLoadingHistory || isSending || !draft.trim()}
              >
                {isSending ? "Sending..." : "Send answer"}
              </button>
            </form>
          </div>
        </section>
      </div>
    </main>
  );
}
