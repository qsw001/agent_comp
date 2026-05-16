/**
 * API 客户端
 */
import axios, { AxiosError, type AxiosInstance, type AxiosRequestConfig } from "axios";
import type { ApiResponse } from "@/types";

const BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: `${BASE_URL}/api/v1`,
      timeout: 30_000,
      headers: {
        "Content-Type": "application/json",
      },
    });

    this.client.interceptors.request.use((config) => {
      // 从 localStorage 读取 token
      const token =
        typeof window !== "undefined" ? localStorage.getItem("auth_token") : null;
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    });

    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError<ApiResponse<never>>) => {
        if (error.response?.status === 401) {
          // Token 过期，清除并跳转登录
          if (typeof window !== "undefined") {
            localStorage.removeItem("auth_token");
            window.location.href = "/login";
          }
        }
        return Promise.reject(error);
      }
    );
  }

  async get<T>(url: string, config?: AxiosRequestConfig): Promise<ApiResponse<T>> {
    const response = await this.client.get<ApiResponse<T>>(url, config);
    return response.data;
  }

  async post<T>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<ApiResponse<T>> {
    const response = await this.client.post<ApiResponse<T>>(url, data, config);
    return response.data;
  }

  async put<T>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<ApiResponse<T>> {
    const response = await this.client.put<ApiResponse<T>>(url, data, config);
    return response.data;
  }

  async delete<T>(url: string, config?: AxiosRequestConfig): Promise<ApiResponse<T>> {
    const response = await this.client.delete<ApiResponse<T>>(url, config);
    return response.data;
  }

  /**
   * SSE 流式请求（用于对话/AI 回复）
   */
  async stream(
    url: string,
    body: unknown,
    callbacks: {
      onChunk: (text: string) => void;
      onDone: () => void;
      onError: (error: Error) => void;
    }
  ): Promise<AbortController> {
    const controller = new AbortController();

    try {
      const response = await fetch(`${BASE_URL}/api/v1${url}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${
            typeof window !== "undefined" ? localStorage.getItem("auth_token") : ""
          }`,
        },
        body: JSON.stringify(body),
        signal: controller.signal,
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const reader = response.body?.getReader();
      if (!reader) throw new Error("No response body");

      const decoder = new TextDecoder();
      let buffer = "";

      const process = async () => {
        while (true) {
          const { done, value } = await reader.read();
          if (done) {
            callbacks.onDone();
            break;
          }
          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop() || "";

          for (const line of lines) {
            if (line.startsWith("data: ")) {
              const data = line.slice(6).trim();
              if (data === "[DONE]") {
                callbacks.onDone();
                return;
              }
              try {
                const parsed = JSON.parse(data);
                if (parsed.content) {
                  callbacks.onChunk(parsed.content);
                }
              } catch {
                callbacks.onChunk(data);
              }
            }
          }
        }
      };

      process().catch(callbacks.onError);
    } catch (err) {
      callbacks.onError(err instanceof Error ? err : new Error(String(err)));
    }

    return controller;
  }
}

export const api = new ApiClient();
