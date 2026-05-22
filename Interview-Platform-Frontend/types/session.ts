export type StoredInterviewSession = {
  interviewId: string;
  role: string;
  experienceLevel: string;
  difficulty: string;
  interviewType: string;
  interviewMode: string;
  resumeName: string;
  firstQuestion: string;
  startedAt: string;
  status?: "active" | "submitted";
};
