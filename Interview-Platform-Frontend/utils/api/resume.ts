import type { ResumeUploadResponse } from "@/types/api";
import { apiClient } from "./client";

export async function uploadResume(file: File): Promise<ResumeUploadResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await apiClient.post<ResumeUploadResponse>(
    "/resume/upload",
    formData,
    {
      headers: {
        "Content-Type": "multipart/form-data"
      }
    }
  );

  return response.data;
}
