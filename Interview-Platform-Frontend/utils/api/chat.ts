import type {
  InterviewChatRequest,
  InterviewFeedbackResponse,
  InterviewHistoryResponse,
  InterviewQuestionResponse,
  InterviewSessionsResponse,
  InterviewSetupRequest,
  InterviewSetupResponse,
  StartInterviewRequest,
  SubmitInterviewResponse
} from "@/types/api";
import { apiClient } from "./client";

export async function setupInterview(
  payload: InterviewSetupRequest
): Promise<InterviewSetupResponse> {
  const response = await apiClient.post<InterviewSetupResponse>(
    "/interview/setup",
    payload
  );

  return response.data;
}

export async function startInterview(
  payload: StartInterviewRequest
): Promise<InterviewQuestionResponse> {
  const response = await apiClient.post<InterviewQuestionResponse>(
    "/interview/start",
    payload
  );

  return response.data;
}

export async function sendInterviewMessage(
  payload: InterviewChatRequest
): Promise<InterviewQuestionResponse> {
  const response = await apiClient.post<InterviewQuestionResponse>(
    "/interview/chat",
    payload
  );

  return response.data;
}

export async function getInterviewSessions(): Promise<InterviewSessionsResponse> {
  const response = await apiClient.get<InterviewSessionsResponse>(
    "/interview/sessions"
  );

  return response.data;
}

export async function getInterviewHistory(
  interviewId: string
): Promise<InterviewHistoryResponse> {
  const response = await apiClient.get<InterviewHistoryResponse>(
    `/interview/${interviewId}/history`
  );

  return response.data;
}

export async function submitInterview(
  interviewId: string
): Promise<SubmitInterviewResponse> {
  const response = await apiClient.post<SubmitInterviewResponse>(
    `/interview/${interviewId}/submit`
  );

  return response.data;
}

export async function getInterviewFeedback(
  interviewId: string
): Promise<InterviewFeedbackResponse> {
  const response = await apiClient.get<InterviewFeedbackResponse>(
    `/interview/${interviewId}/feedback`
  );

  return response.data;
}
