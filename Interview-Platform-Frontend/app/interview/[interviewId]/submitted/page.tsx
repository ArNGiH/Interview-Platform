"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { getApiErrorMessage } from "@/utils/api/client";
import { getInterviewFeedback } from "@/utils/api/chat";
import type { InterviewFeedback } from "@/types/api";

function formatRecommendation(value: string) {
  return value.replaceAll("_", " ");
}

export default function SubmittedInterviewPage() {
  const params = useParams<{ interviewId: string }>();
  const interviewId = params.interviewId;
  const [feedback, setFeedback] = useState<InterviewFeedback | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let isMounted = true;

    async function loadFeedback() {
      setIsLoading(true);
      setError("");

      try {
        const response = await getInterviewFeedback(interviewId);

        if (isMounted) {
          setFeedback(response.feedback);
        }
      } catch (feedbackError) {
        if (isMounted) {
          setError(getApiErrorMessage(feedbackError, "Could not load feedback"));
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    }

    loadFeedback();

    return () => {
      isMounted = false;
    };
  }, [interviewId]);

  const report = feedback?.report;

  return (
    <main className="page">
      <section className="submitted-shell">
        <p className="eyebrow">Submitted interview</p>
        <h1>{report ? "Feedback report generated." : "Feedback is being prepared."}</h1>
        <p>
          The Feedback Agent reviews the full interview transcript and produces a hiring-style
          assessment across communication, technical signal, behavioral signal, and improvement
          areas.
        </p>

        <div className="submitted-meta">
          <span>Interview ID</span>
          <strong>{interviewId}</strong>
        </div>

        {isLoading ? (
          <div className="empty-state">
            <h2>Loading feedback</h2>
            <p>Checking whether the feedback report is ready.</p>
          </div>
        ) : null}

        {error ? <div className="error-box">{error}</div> : null}

        {!isLoading && report ? (
          <div className="feedback-report">
            <div className="feedback-summary">
              <h2>{formatRecommendation(report.hiring_recommendation)}</h2>
              <p>{report.recommendation_reason}</p>
            </div>

            <div className="score-grid">
              <div>
                <span>Communication</span>
                <strong>{report.communication_score}/10</strong>
              </div>
              <div>
                <span>Technical</span>
                <strong>{report.technical_score}/10</strong>
              </div>
              <div>
                <span>Behavioral</span>
                <strong>{report.behavioral_score}/10</strong>
              </div>
              <div>
                <span>Confidence</span>
                <strong>{report.confidence_level}</strong>
              </div>
            </div>

            <section className="feedback-section">
              <h3>Overall summary</h3>
              <p>{report.overall_summary}</p>
            </section>

            <div className="feedback-columns">
              <section className="feedback-section">
                <h3>Strengths</h3>
                <ul>
                  {report.strengths.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </section>

              <section className="feedback-section">
                <h3>Weaknesses</h3>
                <ul>
                  {report.weaknesses.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </section>
            </div>

            <section className="feedback-section">
              <h3>Improvement roadmap</h3>
              <ul>
                {report.improvement_roadmap.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </section>

            <section className="feedback-section">
              <h3>Hiring committee notes</h3>
              <div className="agent-votes">
                <p>
                  <strong>Technical Interviewer:</strong>{" "}
                  {report.agent_votes.technical_interviewer}
                </p>
                <p>
                  <strong>Behavioral Interviewer:</strong>{" "}
                  {report.agent_votes.behavioral_interviewer}
                </p>
                <p>
                  <strong>Hiring Manager:</strong>{" "}
                  {report.agent_votes.hiring_manager}
                </p>
              </div>
            </section>
          </div>
        ) : null}

        {!isLoading && !report && !error ? (
          <div className="empty-state">
            <h2>No feedback yet</h2>
            <p>Submit the interview from the chat screen to trigger the Feedback Agent.</p>
          </div>
        ) : null}

        <div className="submitted-actions">
          <Link className="button button-secondary" href="/interviews">
            Back to interviews
          </Link>
          <Link className="button button-primary" href="/setup">
            New interview
          </Link>
        </div>
      </section>
    </main>
  );
}
