export type Difficulty = "easy" | "medium" | "hard";

export type InterviewType = "technical" | "behavioral" | "mixed";

export type InterviewMode = "frontend_round" | "backend_round" | "system_design" | "screening";

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

export type ApiErrorResponse = {
  detail?: string;
  message?: string;
};
