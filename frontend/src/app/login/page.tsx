"use client";

import { FormEvent, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { api } from "@/lib/api";

type AuthMode = "login" | "register";

interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}

function saveToken(token: string, expiresInHours: number) {
  const maxAge = expiresInHours * 60 * 60;
  localStorage.setItem("auth_token", token);
  document.cookie = `auth_token=${token}; path=/; max-age=${maxAge}; SameSite=Lax`;
}

export default function LoginPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const next = searchParams.get("next") || "/dashboard";

  const [mode, setMode] = useState<AuthMode>("login");
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function loginWithPassword() {
    const response = await api.post<TokenResponse>("/auth/login", {
      username,
      password,
    });

    if (!response.success || !response.data) {
      throw new Error(response.error?.message || "登录失败");
    }

    saveToken(response.data.access_token, response.data.expires_in);
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setLoading(true);

    try {
      if (mode === "register") {
        const response = await api.post("/auth/register", {
          username,
          email,
          password,
        });

        if (!response.success) {
          throw new Error(response.error?.message || "注册失败");
        }
      }

      await loginWithPassword();
      router.replace(next);
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "请求失败，请稍后再试");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen overflow-hidden">
      <section className="relative flex min-h-screen justify-center">
        <img
          src="https://pagedone.io/asset/uploads/1702362010.png"
          alt="gradient background"
          className="fixed inset-0 h-full w-full object-cover"
        />
        <div className="absolute inset-0 mx-auto flex w-full max-w-md flex-col items-center justify-center px-6 py-10 lg:px-8 lg:py-14">
          <div className="mb-2 text-center text-4xl font-bold leading-10 text-gray-900">
            AI EDU
          </div>

          <div className="w-full rounded-2xl bg-white shadow-xl">
            <form className="mx-auto p-6 lg:p-8" onSubmit={handleSubmit}>
              <div className="mb-6 lg:mb-8">
                <h1 className="mb-2 text-center text-2xl font-bold leading-9 text-gray-900">
                  {mode === "login" ? "欢迎回来" : "创建账号"}
                </h1>
                <p className="text-center text-base font-medium leading-6 text-gray-500">
                  {mode === "login"
                    ? "登录后进入你的个性化学习空间"
                    : "注册后立即开始你的学习之旅"}
                </p>
              </div>

              <div className="mb-5 grid grid-cols-2 rounded-full bg-gray-100 p-1">
                <button
                  type="button"
                  onClick={() => setMode("login")}
                  className={`h-9 rounded-full text-sm font-semibold transition-all ${
                    mode === "login"
                      ? "bg-indigo-600 text-white shadow-sm"
                      : "text-gray-500 hover:text-gray-900"
                  }`}
                >
                  登录
                </button>
                <button
                  type="button"
                  onClick={() => setMode("register")}
                  className={`h-9 rounded-full text-sm font-semibold transition-all ${
                    mode === "register"
                      ? "bg-indigo-600 text-white shadow-sm"
                      : "text-gray-500 hover:text-gray-900"
                  }`}
                >
                  注册
                </button>
              </div>

              <input
                type="text"
                value={username}
                onChange={(event) => setUsername(event.target.value)}
                className="mb-5 h-11 w-full rounded-full border border-gray-300 px-4 text-base font-normal leading-7 text-gray-900 shadow-sm outline-none placeholder:text-gray-400 focus:border-indigo-500"
                placeholder="用户名"
                minLength={2}
                maxLength={64}
                required
              />

              {mode === "register" && (
                <input
                  type="email"
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  className="mb-5 h-11 w-full rounded-full border border-gray-300 px-4 text-base font-normal leading-7 text-gray-900 shadow-sm outline-none placeholder:text-gray-400 focus:border-indigo-500"
                  placeholder="邮箱"
                  required
                />
              )}

              <input
                type="password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                className="mb-1 h-11 w-full rounded-full border border-gray-300 px-4 text-base font-normal leading-7 text-gray-900 shadow-sm outline-none placeholder:text-gray-400 focus:border-indigo-500"
                placeholder="密码"
                minLength={6}
                maxLength={128}
                required
              />

              <a href="#" className="mb-5 flex justify-end">
                <span className="text-right text-sm font-normal leading-6 text-indigo-600">
                  忘记密码？
                </span>
              </a>

              {error && (
                <p className="mb-5 rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-600">
                  {error}
                </p>
              )}

              <button
                type="submit"
                disabled={loading}
                className="mb-8 h-11 w-full rounded-full bg-indigo-600 text-center text-base font-semibold leading-6 text-white shadow-sm transition-all duration-700 hover:bg-indigo-800 disabled:cursor-not-allowed disabled:opacity-70"
              >
                {loading ? "处理中..." : mode === "login" ? "登录" : "注册"}
              </button>

              <button
                type="button"
                onClick={() => setMode(mode === "login" ? "register" : "login")}
                className="flex w-full justify-center text-sm font-medium leading-6 text-gray-900"
              >
                {mode === "login" ? "还没有账号？" : "已经有账号？"}
                <span className="pl-3 font-semibold text-indigo-600">
                  {mode === "login" ? "去注册" : "去登录"}
                </span>
              </button>
            </form>
          </div>
        </div>
      </section>
    </main>
  );
}
