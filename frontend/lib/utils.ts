import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDate(date: string | Date): string {
  return new Date(date).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

export function formatRelativeTime(date: string | Date): string {
  const now = new Date();
  const d = new Date(date);
  const diffMs = now.getTime() - d.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffMins < 1) return "just now";
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;
  return formatDate(date);
}

export function getScoreColor(score: number): string {
  if (score >= 80) return "text-green-500";
  if (score >= 60) return "text-yellow-500";
  if (score >= 40) return "text-orange-500";
  return "text-red-500";
}

export function getScoreLabel(score: number): string {
  if (score >= 80) return "Excellent";
  if (score >= 60) return "Good";
  if (score >= 40) return "Fair";
  if (score > 0) return "Poor";
  return "No data";
}

export function getStatusBadgeVariant(status: string) {
  switch (status) {
    case "active":
      return "bg-green-100 text-green-700 border-green-200";
    case "paused":
      return "bg-yellow-100 text-yellow-700 border-yellow-200";
    case "needs_recovery":
      return "bg-red-100 text-red-700 border-red-200";
    case "error":
      return "bg-red-100 text-red-700 border-red-200";
    case "inactive":
      return "bg-gray-100 text-gray-600 border-gray-200";
    default:
      return "bg-gray-100 text-gray-600 border-gray-200";
  }
}

export function getStatusLabel(status: string): string {
  const labels: Record<string, string> = {
    active: "Active",
    paused: "Paused",
    needs_recovery: "Needs Recovery",
    inactive: "Inactive",
    error: "Connection Error",
    connecting: "Connecting",
  };
  return labels[status] || status;
}

export function getESPIcon(esp: string): string {
  switch (esp.toLowerCase()) {
    case "google": return "G";
    case "microsoft": return "M";
    default: return "O";
  }
}

export function formatNumber(n: number): string {
  if (n >= 1000000) return `${(n / 1000000).toFixed(1)}M`;
  if (n >= 1000) return `${(n / 1000).toFixed(1)}K`;
  return n.toString();
}
