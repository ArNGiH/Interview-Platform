"use client";

import { FormEvent, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { setupInterview, startInterview } from "@/utils/api/chat";
import { getApiErrorMessage } from "@/utils/api/client";
import { uploadResume } from "@/utils/api/resume";
import type { InterviewMode, InterviewType, Difficulty } from "@/types/api";

const roleOptions = [
  "Frontend Developer",
  "Backend Developer",
  "Full Stack Developer",
  "Machine Learning Engineer",
  "DevOps Engineer"
];

const experienceOptions = ["Intern", "0-1 year", "1 year", "2-3 years", "4-6 years", "7+ years"];

export default function SetupPage() {
  const router = useRouter();
  const [role, setRole] = useState(roleOptions[0]);
  const [experienceLevel, setExperienceLevel] = useState("1 year");
  const [difficulty, setDifficulty] = useState<Difficulty>("medium");
  const [interviewType, setInterviewType] = useState<InterviewType>("technical");
  const [interviewMode, setInterviewMode] = useState<InterviewMode>("frontend_round");
  const [jobDescription, setJobDescription] = useState("");
  const [resumeId, setResumeId] = useState<string | null>(null);
  const [resumeName, setResumeName] = useState("");
  const [isUploading, setIsUploading] = useState(false);
  const [isStarting, setIsStarting] = useState(false);
  const [error, setError] = useState("");

  const canStart = useMemo(() => {
    return role.trim() && experienceLevel.trim() && !isUploading && !isStarting;
  }, [role, experienceLevel, isUploading, isStarting]);

  async function handleResumeChange(file: File | null) {
    if (!file) {
      return;
    }

    setError("");
    setIsUploading(true);

    try {
      const response = await uploadResume(file);
      setResumeId(response.resume_id);
      setResumeName(response.filename);
    } catch (uploadError) {
      setError(getApiErrorMessage(uploadError, "Resume upload failed"));
    } finally {
      setIsUploading(false);
    }
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setIsStarting(true);

    try {
      const setupResponse = await setupInterview({
        role,
        experience_level: experienceLevel,
        difficulty,
        interview_type: interviewType,
        interview_mode: interviewMode,
        resume_id: resumeId,
        resume_uploaded: Boolean(resumeId),
        job_description_provided: Boolean(jobDescription.trim())
      });

      const startResponse = await startInterview({
        interview_id: setupResponse.interview_id
      });

      sessionStorage.setItem(
        `interview:${setupResponse.interview_id}`,
        JSON.stringify({
          interviewId: setupResponse.interview_id,
          role,
          experienceLevel,
          difficulty,
          interviewType,
          interviewMode,
          resumeName,
          firstQuestion: startResponse.question,
          startedAt: new Date().toISOString()
        })
      );

      router.push(`/interview/${setupResponse.interview_id}`);
    } catch (setupError) {
      setError(getApiErrorMessage(setupError, "Could not start interview"));
    } finally {
      setIsStarting(false);
    }
  }

  return (
    <main className="page">
      <div className="section-header">
        <div>
          <p className="eyebrow">Interview setup</p>
          <h1>Configure the round before the first question.</h1>
          <p>
            Upload the candidate resume, choose the interview shape, and start a session that the
            backend can ground in resume context.
          </p>
        </div>
      </div>

      <form className="setup-layout" onSubmit={handleSubmit}>
        <section className="panel">
          <div className="panel-header">
            <h2>Candidate and round details</h2>
            <p>These values map directly to the interview setup API.</p>
          </div>

          <div className="panel-body">
            <div className="form-grid">
              <div className="field">
                <label htmlFor="role">Role</label>
                <select id="role" value={role} onChange={(event) => setRole(event.target.value)}>
                  {roleOptions.map((option) => (
                    <option key={option} value={option}>
                      {option}
                    </option>
                  ))}
                </select>
              </div>

              <div className="field">
                <label htmlFor="experience">Experience level</label>
                <select
                  id="experience"
                  value={experienceLevel}
                  onChange={(event) => setExperienceLevel(event.target.value)}
                >
                  {experienceOptions.map((option) => (
                    <option key={option} value={option}>
                      {option}
                    </option>
                  ))}
                </select>
              </div>

              <div className="field">
                <label htmlFor="difficulty">Difficulty</label>
                <select
                  id="difficulty"
                  value={difficulty}
                  onChange={(event) => setDifficulty(event.target.value as Difficulty)}
                >
                  <option value="easy">Easy</option>
                  <option value="medium">Medium</option>
                  <option value="hard">Hard</option>
                </select>
              </div>

              <div className="field">
                <label htmlFor="interviewType">Interview type</label>
                <select
                  id="interviewType"
                  value={interviewType}
                  onChange={(event) => setInterviewType(event.target.value as InterviewType)}
                >
                  <option value="technical">Technical</option>
                  <option value="behavioral">Behavioral</option>
                  <option value="mixed">Mixed</option>
                </select>
              </div>

              <div className="field">
                <label htmlFor="interviewMode">Interview mode</label>
                <select
                  id="interviewMode"
                  value={interviewMode}
                  onChange={(event) => setInterviewMode(event.target.value as InterviewMode)}
                >
                  <option value="frontend_round">Frontend round</option>
                  <option value="backend_round">Backend round</option>
                  <option value="system_design">System design</option>
                  <option value="screening">Screening</option>
                </select>
              </div>

              <div className="field">
                <label htmlFor="resume">Resume PDF</label>
                <label className="dropzone" htmlFor="resume">
                  <span>
                    <strong>{resumeName || "Upload a resume"}</strong>
                    {isUploading
                      ? "Uploading and embedding resume..."
                      : "PDF upload calls /resume/upload and stores the returned resume ID."}
                  </span>
                  <input
                    className="hidden-input"
                    id="resume"
                    type="file"
                    accept="application/pdf"
                    onChange={(event) => handleResumeChange(event.target.files?.[0] || null)}
                  />
                </label>
              </div>

              <div className="field full">
                <label htmlFor="jobDescription">Job description notes</label>
                <textarea
                  id="jobDescription"
                  value={jobDescription}
                  onChange={(event) => setJobDescription(event.target.value)}
                  placeholder="Optional. Your current backend records whether a job description exists."
                />
              </div>
            </div>

            {error ? <div className="error-box">{error}</div> : null}

            <div className="setup-footer">
              <span className="status-pill">
                <span className={`status-dot ${resumeId ? "status-dot-online" : ""}`} />
                {resumeId ? "Resume attached" : "Resume optional"}
              </span>

              <button className="button button-primary" type="submit" disabled={!canStart}>
                {isStarting ? "Starting interview..." : "Start interview"}
              </button>
            </div>
          </div>
        </section>

        <aside className="panel">
          <div className="panel-header">
            <h3>Session summary</h3>
            <p>The interview will start immediately after setup.</p>
          </div>

          <div className="panel-body">
            <div className="summary-list">
              <div className="summary-item">
                <span>Role</span>
                <strong>{role}</strong>
              </div>
              <div className="summary-item">
                <span>Experience</span>
                <strong>{experienceLevel}</strong>
              </div>
              <div className="summary-item">
                <span>Difficulty</span>
                <strong>{difficulty}</strong>
              </div>
              <div className="summary-item">
                <span>Mode</span>
                <strong>{interviewMode.replace("_", " ")}</strong>
              </div>
              <div className="summary-item">
                <span>Resume ID</span>
                <strong>{resumeId ? `${resumeId.slice(0, 8)}...` : "None"}</strong>
              </div>
            </div>
          </div>
        </aside>
      </form>
    </main>
  );
}
