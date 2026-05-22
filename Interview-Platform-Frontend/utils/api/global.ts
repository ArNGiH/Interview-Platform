import type { ApiHealthResponse } from "@/types/api";
import { apiClient } from "./client";

export async function getApiHealth(): Promise<ApiHealthResponse> {
  const response = await apiClient.get<ApiHealthResponse>("/");

  return response.data;
}
