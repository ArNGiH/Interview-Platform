export type Difficulty = "easy" | "medium" | "hard";

export type InterviewType = "technical" | "behavioral" | "mixed";

export type InterviewMode = "frontend_round" | "backend_round" | "system_design" | "screening";

export type InterviewStatus = "active" | "submitted";

export type ApiHealthResponse = {
  status: string;
};

export type ResumeUploadResponse = {
  resume_id: string;
  filename: string;
  status: string;
};

export type InterviewSetupRequest = {
  role: string;
  experience_level: string;
  difficulty: string;
  interview_type: string;
  interview_mode: string;
  resume_id: string | null;
  resume_uploaded: boolean;
  job_description_provided: boolean;
};

export type InterviewSetupResponse = {
  interview_id: string;
  status: string;
};

export type StartInterviewRequest = {
  interview_id: string;
};

export type InterviewQuestionResponse = {
  interview_id: string;
  question: string;
};

export type InterviewChatRequest = {
  interview_id: string;
  message: string;
};

export type InterviewMessage = {
  id: string;
  role: "assistant" | "user";
  content: string;
  createdAt: string;
};

export type InterviewSessionSummary = {
  interview_id: string;
  role: string;
  experience_level: string;
  difficulty: string;
  interview_type: string;
  interview_mode: string;
  status: InterviewStatus;
  resume_uploaded: boolean;
  job_description_provided: boolean;
  created_at: string | null;
  last_message_at: string | null;
  message_count: number;
};

export type InterviewSessionsResponse = {
  sessions: InterviewSessionSummary[];
};

export type InterviewHistoryMessage = {
  id: string;
  role: "assistant" | "user";
  content: string;
  created_at: string | null;
};

export type InterviewHistoryResponse = {
  session: InterviewSessionSummary;
  messages: InterviewHistoryMessage[];
};

export type InterviewFeedbackReport = {
  overall_summary: string;
  strengths: string[];
  weaknesses: string[];
  communication_score: number;
  technical_score: number;
  behavioral_score: number;
  confidence_level: "LOW" | "MEDIUM" | "HIGH";
  hiring_recommendation:
    | "STRONG_NO"
    | "NO"
    | "LEAN_NO"
    | "LEAN_YES"
    | "YES"
    | "STRONG_YES";
  recommendation_reason: string;
  improvement_roadmap: string[];
  agent_votes: {
    technical_interviewer: string;
    behavioral_interviewer: string;
    hiring_manager: string;
  };
};

export type InterviewFeedback = {
  id: string;
  interview_id: string;
  report: InterviewFeedbackReport;
  created_at: string | null;
};

export type SubmitInterviewResponse = {
  session: InterviewSessionSummary;
  feedback: InterviewFeedback | null;
};

export type InterviewFeedbackResponse = {
  feedback: InterviewFeedback | null;
};

export type ApiErrorResponse = {
  detail?: string;
  message?: string;
};
