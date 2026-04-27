import axios, { AxiosInstance, AxiosError } from "axios";
import Cookies from "js-cookie";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const api: AxiosInstance = axios.create({
  baseURL: `${BASE_URL}/api/v1`,
  headers: { "Content-Type": "application/json" },
  timeout: 30000,
});

// Attach access token to every request
api.interceptors.request.use((config) => {
  const token = Cookies.get("access_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Auto-refresh on 401
api.interceptors.response.use(
  (res) => res,
  async (error: AxiosError) => {
    if (error.response?.status === 401) {
      const refresh = Cookies.get("refresh_token");
      if (refresh) {
        try {
          const res = await axios.post(`${BASE_URL}/api/v1/auth/refresh`, {
            refresh_token: refresh,
          });
          const { access_token, refresh_token } = res.data;
          Cookies.set("access_token", access_token, { expires: 1, sameSite: "Strict" });
          Cookies.set("refresh_token", refresh_token, { expires: 30, sameSite: "Strict" });
          if (error.config) {
            error.config.headers.Authorization = `Bearer ${access_token}`;
            return api.request(error.config);
          }
        } catch {
          Cookies.remove("access_token");
          Cookies.remove("refresh_token");
          window.location.href = "/auth/login";
        }
      } else {
        window.location.href = "/auth/login";
      }
    }
    return Promise.reject(error);
  }
);

// — Auth
export const authApi = {
  login: (email: string, password: string) =>
    api.post("/auth/login", { email, password }),
  register: (email: string, password: string, full_name: string) =>
    api.post("/auth/register", { email, password, full_name }),
  me: () => api.get("/users/me"),
};

// — Accounts
export const accountsApi = {
  list: () => api.get("/accounts"),
  get: (id: number) => api.get(`/accounts/${id}`),
  create: (data: unknown) => api.post("/accounts", data),
  update: (id: number, data: unknown) => api.put(`/accounts/${id}`, data),
  delete: (id: number) => api.delete(`/accounts/${id}`),
  testConnection: (id: number) => api.post(`/accounts/${id}/test-connection`),
  enableWarmup: (id: number) => api.post(`/accounts/${id}/enable-warmup`),
  pauseWarmup: (id: number) => api.post(`/accounts/${id}/pause-warmup`),
  resumeWarmup: (id: number) => api.post(`/accounts/${id}/resume-warmup`),
};

// — Analytics
export const analyticsApi = {
  overview: () => api.get("/analytics/overview"),
  accountReport: (id: number, days = 7) =>
    api.get(`/analytics/accounts/${id}/report?days=${days}`),
};

// — Admin / AI Settings
export const adminApi = {
  getAISettings: () => api.get("/admin/ai-settings"),
  updateAISettings: (data: unknown) => api.put("/admin/ai-settings", data),
  getAvailableModels: () => api.get("/admin/ai-settings/models"),
  getGlobalAISettings: () => api.get("/admin/global-ai-settings"),
  updateGlobalAISettings: (data: unknown) => api.put("/admin/global-ai-settings", data),
  getUsers: () => api.get("/admin/users"),
  getStats: () => api.get("/admin/stats"),
};

export type ApiError = AxiosError<{ detail: string | { msg: string }[] }>;

export function getErrorMessage(err: unknown): string {
  const e = err as ApiError;
  if (e?.response?.data?.detail) {
    const detail = e.response.data.detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail)) return detail.map((d) => d.msg).join(", ");
  }
  return "An unexpected error occurred";
}
