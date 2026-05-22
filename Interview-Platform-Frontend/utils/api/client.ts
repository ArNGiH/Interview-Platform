import axios, { AxiosError } from "axios";

const DEFAULT_SERVER_URL = "http://127.0.0.1:8000";

export const apiClient = axios.create({
  baseURL: (process.env.NEXT_PUBLIC_SERVER_URL || DEFAULT_SERVER_URL).replace(/\/$/, ""),
  timeout: 120000
});

export function getApiErrorMessage(error: unknown, fallback: string) {
  if (axios.isAxiosError(error)) {
    const axiosError = error as AxiosError<{
      detail?: string;
      message?: string;
    }>;

    const payload = axiosError.response?.data;

    return payload?.detail || payload?.message || axiosError.message || fallback;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return fallback;
}
