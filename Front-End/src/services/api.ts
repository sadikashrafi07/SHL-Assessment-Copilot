import axios, { AxiosError, type AxiosInstance } from "axios";
import type {
  APIError,
  ChatRequest,
  ChatRequestMessage,
  ChatResponse,
} from "@/types";

const BASE_URL =
  (typeof import.meta !== "undefined" &&
    (import.meta as unknown as { env?: Record<string, string> }).env
      ?.VITE_API_BASE_URL) ||
  "http://localhost:8000/api";

const client: AxiosInstance = axios.create({
  baseURL: BASE_URL,
  timeout: 60_000,
  headers: { "Content-Type": "application/json" },
});

client.interceptors.response.use(
  (res) => res,
  (error: AxiosError) => {
    const apiErr: APIError = {
      message:
        (error.response?.data as { detail?: string } | undefined)?.detail ||
        error.message ||
        "Unexpected error",
      status: error.response?.status,
      detail: error.response?.data,
    };
    return Promise.reject(apiErr);
  },
);

export const api = {
  async chat(messages: ChatRequestMessage[]): Promise<ChatResponse> {
    const body: ChatRequest = { messages };
    const { data } = await client.post<ChatResponse>("/chat", body);
    return data;
  },
  async health(): Promise<{ ok: boolean; raw?: unknown }> {
    try {
      const { data } = await client.get("/health", { timeout: 5000 });
      return { ok: true, raw: data };
    } catch {
      return { ok: false };
    }
  },
  baseUrl: BASE_URL,
};
