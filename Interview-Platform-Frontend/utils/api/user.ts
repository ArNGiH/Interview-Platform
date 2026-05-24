import type { UserInfoResponse } from "@/types/api";
import { apiClient } from "./client";


export async function getUserInfo(): Promise<UserInfoResponse> {
  const response = await apiClient.get<UserInfoResponse>(
    "/user/info"
  );

  return response.data;
}
