"use client";

import { FormEvent, Suspense, useState, useEffect, useRef } from "react";
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

function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const next = searchParams.get("next") || "/dashboard";

  const [mode, setMode] = useState<AuthMode>("login");
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  // ── 验证码状态 ──
  const [codeSent, setCodeSent] = useState(false);
  const [emailCode, setEmailCode] = useState("");
  const [codeVerified, setCodeVerified] = useState(false);
  const [sendingCode, setSendingCode] = useState(false);
  const [verifyingCode, setVerifyingCode] = useState(false);
  const [countdown, setCountdown] = useState(0);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  // 倒计时清理
  useEffect(() => {
    if (countdown > 0) {
      timerRef.current = setInterval(() => {
        setCountdown((c) => {
          if (c <= 1) {
            if (timerRef.current) clearInterval(timerRef.current);
            return 0;
          }
          return c - 1;
        });
      }, 1000);
    }
    return () => { if (timerRef.current) clearInterval(timerRef.current); };
  }, [countdown]);

  // 切换模式时重置验证码状态
  const switchMode = (m: AuthMode) => {
    setMode(m);
    setError("");
    setCodeSent(false);
    setEmailCode("");
    setCodeVerified(false);
    setCountdown(0);
  };

  // ── 发送验证码 ──
  async function handleSendCode() {
    if (!email || sendingCode) return;
    setSendingCode(true);
    setError("");
    try {
      await api.post("/auth/send-email-code", { email });
      setCodeSent(true);
      setCountdown(60);
    } catch (err: any) {
      setError(err?.response?.data?.error?.message || "发送验证码失败");
    } finally {
      setSendingCode(false);
    }
  }

  // ── 校验验证码 ──
  async function handleVerifyCode() {
    if (!emailCode || verifyingCode) return;
    setVerifyingCode(true);
    setError("");
    try {
      await api.post("/auth/verify-email-code", { email, code: emailCode });
      setCodeVerified(true);
    } catch (err: any) {
      setError(err?.response?.data?.error?.message || "验证码错误");
    } finally {
      setVerifyingCode(false);
    }
  }

  // ── 登录 ──
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

  // ── 开发测试登录（跳过密码） ──
  const [devLogging, setDevLogging] = useState(false);
  async function handleDevLogin() {
    if (!username || devLogging) return;
    setDevLogging(true);
    setError("");
    try {
      const response = await api.post<TokenResponse>("/auth/dev-login", {
        username,
      });
      if (!response.success || !response.data) {
        throw new Error(response.error?.message || "测试登录失败");
      }
      saveToken(response.data.access_token, response.data.expires_in);
      router.replace(next);
      router.refresh();
    } catch (err: any) {
      setError(err?.response?.data?.error?.message || err?.message || "测试登录失败");
    } finally {
      setDevLogging(false);
    }
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setLoading(true);

    try {
      if (mode === "register") {
        if (!codeVerified) {
          throw new Error("请先验证邮箱");
        }
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
                  onClick={() => switchMode("login")}
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
                  onClick={() => switchMode("register")}
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
                <>
                  {/* 邮箱 + 发送验证码 */}
                  <div className="mb-3 flex gap-2">
                    <input
                      type="email"
                      value={email}
                      onChange={(event) => {
                        setEmail(event.target.value);
                        setCodeSent(false);
                        setCodeVerified(false);
                      }}
                      className="h-11 flex-1 rounded-full border border-gray-300 px-4 text-base font-normal leading-7 text-gray-900 shadow-sm outline-none placeholder:text-gray-400 focus:border-indigo-500"
                      placeholder="邮箱"
                      required
                    />
                    <button
                      type="button"
                      onClick={handleSendCode}
                      disabled={!email || sendingCode || countdown > 0}
                      className={`shrink-0 rounded-full px-4 text-sm font-semibold transition-all ${
                        countdown > 0
                          ? "bg-gray-200 text-gray-500 cursor-not-allowed"
                          : "bg-indigo-50 text-indigo-600 hover:bg-indigo-100"
                      } disabled:opacity-70`}
                    >
                      {sendingCode ? "发送中" : countdown > 0 ? `${countdown}s` : "发送验证码"}
                    </button>
                  </div>

                  {/* 验证码输入 + 校验按钮 */}
                  {codeSent && !codeVerified && (
                    <div className="mb-3 flex gap-2">
                      <input
                        type="text"
                        value={emailCode}
                        onChange={(event) => setEmailCode(event.target.value.replace(/\D/g, "").slice(0, 6))}
                        className="h-11 flex-1 rounded-full border border-gray-300 px-4 text-center text-lg tracking-[0.3em] font-mono text-gray-900 shadow-sm outline-none placeholder:text-gray-400 focus:border-indigo-500"
                        placeholder="000000"
                        maxLength={6}
                      />
                      <button
                        type="button"
                        onClick={handleVerifyCode}
                        disabled={emailCode.length !== 6 || verifyingCode}
                        className="shrink-0 rounded-full bg-indigo-600 px-5 text-sm font-semibold text-white transition-all hover:bg-indigo-700 disabled:opacity-50"
                      >
                        {verifyingCode ? "校验中" : "验证"}
                      </button>
                    </div>
                  )}

                  {/* 验证成功提示 */}
                  {codeVerified && (
                    <div className="mb-5 flex items-center gap-2 rounded-full bg-emerald-50 px-4 py-2.5 text-sm text-emerald-700">
                      <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                      邮箱已验证
                    </div>
                  )}
                </>
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
                className="mb-2 h-11 w-full rounded-full bg-indigo-600 text-center text-base font-semibold leading-6 text-white shadow-sm transition-all duration-700 hover:bg-indigo-800 disabled:cursor-not-allowed disabled:opacity-70"
              >
                {loading ? "处理中..." : mode === "login" ? "登录" : "注册"}
              </button>

              {mode === "login" && (
                <button
                  type="button"
                  onClick={handleDevLogin}
                  disabled={!username || devLogging}
                  className="mb-8 h-11 w-full rounded-full border-2 border-dashed border-amber-400 bg-amber-50 text-center text-base font-semibold leading-6 text-amber-700 transition-all hover:bg-amber-100 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {devLogging ? "登录中..." : "🔧 测试登录（免密码）"}
                </button>
              )}

              <button
                type="button"
                onClick={() => switchMode(mode === "login" ? "register" : "login")}
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

export default function LoginPage() {
  return (
    <Suspense fallback={
      <main className="min-h-screen flex items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-indigo-600 border-t-transparent" />
      </main>
    }>
      <LoginForm />
    </Suspense>
  );
}
