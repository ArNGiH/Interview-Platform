import type {
  InterviewChatRequest,
  InterviewFeedbackResponse,
  InterviewHistoryResponse,
  InterviewSessionsResponse,
  InterviewSetupRequest,
  InterviewSetupResponse,
  StartInterviewRequest,
  SubmitInterviewResponse
} from "@/types/api";
import { apiClient } from "./client";

const DEFAULT_SERVER_URL = "http://127.0.0.1:8000";

function getServerUrl(path: string) {
  const baseUrl = (process.env.NEXT_PUBLIC_SERVER_URL || DEFAULT_SERVER_URL).replace(/\/$/, "");

  return `${baseUrl}${path}`;
}

function parseStreamPayload(payload: string) {
  if (!payload || payload === "[DONE]") {
    return "";
  }

  try {
    const parsed = JSON.parse(payload) as {
      token?: unknown;
      content?: unknown;
      text?: unknown;
    };

    if (typeof parsed.token === "string") {
      return parsed.token;
    }

    if (typeof parsed.content === "string") {
      return parsed.content;
    }

    if (typeof parsed.text === "string") {
      return parsed.text;
    }
  } catch {
    return payload;
  }

  return "";
}

function getEventData(eventText: string) {
  const dataLines: string[] = [];

  for (const line of eventText.split("\n")) {
    if (!line.startsWith("data:")) {
      continue;
    }

    let value = line.slice(5);

    if (value.startsWith(" ")) {
      value = value.slice(1);
    }

    dataLines.push(value);
  }

  return dataLines.join("\n");
}

function normalizeSseBuffer(buffer: string) {
  return buffer.replace(/\r\n/g, "\n").replace(/\r/g, "\n");
}

export function cleanStreamedText(value: string) {
  if (!/^data:/m.test(value)) {
    return value;
  }

  let cleaned = "";
  const normalized = normalizeSseBuffer(value);
  const events = normalized.split("\n\n");

  for (const eventText of events) {
    const payload = getEventData(eventText);
    cleaned += parseStreamPayload(payload);
  }

  return cleaned || value;
}

async function streamInterviewResponse(
  path: string,
  payload: unknown,
  onChunk: (chunk: string) => void
) {
  const response = await fetch(
    getServerUrl(path),
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    }
  );

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || `Request failed with status ${response.status}`);
  }

  if (!response.body) {
    throw new Error("Streaming response body missing");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  function flushEvent(eventText: string) {
    const payloadText = getEventData(eventText);
    const chunk = parseStreamPayload(payloadText);

    if (chunk) {
      onChunk(chunk);
    }
  }

  while (true) {
    const { done, value } = await reader.read();

    if (done) {
      break;
    }

    buffer = normalizeSseBuffer(buffer + decoder.decode(value, { stream: true }));

    let eventEndIndex = buffer.indexOf("\n\n");

    while (eventEndIndex !== -1) {
      const eventText = buffer.slice(0, eventEndIndex);
      buffer = buffer.slice(eventEndIndex + 2);
      flushEvent(eventText);
      eventEndIndex = buffer.indexOf("\n\n");
    }
  }

  buffer = normalizeSseBuffer(buffer + decoder.decode());

  if (buffer.trim()) {
    flushEvent(buffer);
  }
}

export async function setupInterview(
  payload: InterviewSetupRequest
): Promise<InterviewSetupResponse> {
  const response = await apiClient.post<InterviewSetupResponse>(
    "/interview/setup",
    payload
  );

  return response.data;
}

export async function streamStartInterview(
  payload: StartInterviewRequest,
  onChunk: (chunk: string) => void
): Promise<void> {
  return streamInterviewResponse("/interview/start", payload, onChunk);
}

export async function streamInterviewMessage(
  payload: InterviewChatRequest,
  onChunk: (chunk: string) => void
): Promise<void> {
  return streamInterviewResponse("/interview/chat", payload, onChunk);
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
