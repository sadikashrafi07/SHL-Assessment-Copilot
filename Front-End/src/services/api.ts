import axios, { AxiosError, type AxiosInstance } from "axios";
import type {
  APIError,
  ChatRequest,
  ChatRequestMessage,
  ChatResponse,
} from "@/types";

/**
 * Read API URL only from environment variables
 */
const env =
  typeof import.meta !== "undefined"
    ? (import.meta as ImportMeta & {
        env: Record<string, string | undefined>;
      }).env
    : undefined;

const BASE_URL = env?.VITE_API_BASE_URL?.trim();

if (!BASE_URL) {
  throw new Error(
    "Missing VITE_API_BASE_URL environment variable.",
  );
}

const client: AxiosInstance = axios.create({
  baseURL: BASE_URL,
  timeout: 60_000,
  headers: {
    "Content-Type": "application/json",
  },
});

/**
 * Global response error handler
 */
client.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    const apiError: APIError = {
      message:
        (error.response?.data as { detail?: string } | undefined)?.detail ||
        error.message ||
        "Unexpected API error",
      status: error.response?.status,
      detail: error.response?.data,
    };

    return Promise.reject(apiError);
  },
);

export const api = {
  /**
   * Chat API
   */
  async chat(messages: ChatRequestMessage[]): Promise<ChatResponse> {
    const body: ChatRequest = { messages };

    const { data } = await client.post<ChatResponse>(
      "/chat",
      body,
    );

    return data;
  },

  /**
   * Health check
   */
  async health(): Promise<{ ok: boolean; raw?: unknown }> {
    try {
      const { data } = await client.get("/health", {
        timeout: 5000,
      });

      return {
        ok: true,
        raw: data,
      };
    } catch {
      return {
        ok: false,
      };
    }
  },

  /**
   * Expose resolved base URL
   */
  baseUrl: BASE_URL,
};

export default client;