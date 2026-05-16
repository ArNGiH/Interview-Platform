import type {
  ApiHealthResponse,
  InterviewChatRequest,
  InterviewQuestionResponse,
  InterviewSetupRequest,
  InterviewSetupResponse,
  ResumeUploadResponse,
  StartInterviewRequest
} from "@/types/api";

async function parseResponse<T>(response: Response): Promise<T> {
  const contentType = response.headers.get("content-type") || "";
  const payload = contentType.includes("application/json")
    ? await response.json()
    : await response.text();

  if (!response.ok) {
    const message =
      typeof payload === "string"
        ? payload
        : payload.detail || payload.message || "Request failed";

    throw new Error(message);
  }

  return payload as T;
}

export async function getApiHealth(): Promise<ApiHealthResponse> {
  const response = await fetch("/api/backend/health", {
    cache: "no-store"
  });

  return parseResponse<ApiHealthResponse>(response);
}

export async function uploadResume(file: File): Promise<ResumeUploadResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch("/api/backend/resume/upload", {
    method: "POST",
    body: formData
  });

  return parseResponse<ResumeUploadResponse>(response);
}

export async function setupInterview(
  payload: InterviewSetupRequest
): Promise<InterviewSetupResponse> {
  const response = await fetch("/api/backend/interview/setup", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });

  return parseResponse<InterviewSetupResponse>(response);
}

export async function startInterview(
  payload: StartInterviewRequest
): Promise<InterviewQuestionResponse> {
  const response = await fetch("/api/backend/interview/start", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });

  return parseResponse<InterviewQuestionResponse>(response);
}

export async function sendInterviewMessage(
  payload: InterviewChatRequest
): Promise<InterviewQuestionResponse> {
  const response = await fetch("/api/backend/interview/chat", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });

  return parseResponse<InterviewQuestionResponse>(response);
}
