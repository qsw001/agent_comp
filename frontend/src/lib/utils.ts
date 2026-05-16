import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

/**
 * 合并 Tailwind class（处理冲突）
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/**
 * 格式化时间
 */
export function formatDate(date: string | Date, options?: Intl.DateTimeFormatOptions) {
  const d = typeof date === "string" ? new Date(date) : date;
  return d.toLocaleDateString("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    ...options,
  });
}

/**
 * 格式化相对时间
 */
export function timeAgo(date: string | Date): string {
  const now = Date.now();
  const then = new Date(date).getTime();
  const diff = now - then;

  const minutes = Math.floor(diff / 60000);
  if (minutes < 1) return "刚刚";
  if (minutes < 60) return `${minutes} 分钟前`;

  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours} 小时前`;

  const days = Math.floor(hours / 24);
  if (days < 30) return `${days} 天前`;

  return formatDate(date);
}

/**
 * 难度标签映射
 */
export const difficultyLabels: Record<number, { label: string; color: string }> = {
  1: { label: "入门", color: "bg-green-100 text-green-700" },
  2: { label: "简单", color: "bg-blue-100 text-blue-700" },
  3: { label: "中等", color: "bg-yellow-100 text-yellow-700" },
  4: { label: "困难", color: "bg-orange-100 text-orange-700" },
  5: { label: "进阶", color: "bg-red-100 text-red-700" },
};

/**
 * 安全解析 JSON（避免 try-catch 坨代码）
 */
export function safeJsonParse<T>(str: string, fallback: T): T {
  try {
    return JSON.parse(str) as T;
  } catch {
    return fallback;
  }
}
