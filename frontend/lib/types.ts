export interface User {
  id: number;
  email: string;
  full_name: string;
  is_active: boolean;
  is_admin: boolean;
  timezone: string;
  avatar_url?: string;
  created_at: string;
}

export interface EmailAccount {
  id: number;
  user_id: number;
  email: string;
  display_name?: string;
  provider: "gmail" | "outlook" | "yahoo" | "custom";
  smtp_host: string;
  smtp_port: number;
  smtp_use_tls: boolean;
  imap_host: string;
  imap_port: number;
  imap_use_ssl: boolean;
  username: string;
  warming_enabled: boolean;
  status: AccountStatus;
  daily_warmup_limit: number;
  ramp_up_days: number;
  current_warmup_day: number;
  emails_sent_today: number;
  warmup_start_date?: string;
  last_warmup_at?: string;
  deliverability_score: number;
  total_sent: number;
  total_inbox: number;
  total_spam_rescued: number;
  target_emails_today: number;
  last_connection_error?: string;
  connection_tested_at?: string;
  created_at: string;
}

export type AccountStatus =
  | "active"
  | "paused"
  | "needs_recovery"
  | "inactive"
  | "error"
  | "connecting";

export interface ConnectionTestResult {
  success: boolean;
  smtp_ok: boolean;
  imap_ok: boolean;
  error?: string;
  latency_ms?: number;
}

export interface ESPStats {
  esp: string;
  total_sent: number;
  inbox: number;
  spam: number;
  other: number;
  undelivered: number;
  replies: number;
  deliverability_rate: number;
  score: number;
}

export interface DailyStats {
  date: string;
  emails_sent: number;
  replies: number;
  inbox: number;
  spam_rescued: number;
  other: number;
  undelivered: number;
}

export interface PlacementBreakdown {
  inbox: number;
  spam_rescued: number;
  other: number;
  undelivered: number;
}

export interface AccountReport {
  account_id: number;
  account_email: string;
  status: string;
  period_days: number;
  total_sent: number;
  total_received: number;
  total_replies: number;
  deliverability_score: number;
  google_score: number;
  microsoft_score: number;
  others_score: number;
  placement: PlacementBreakdown;
  esp_stats: ESPStats[];
  daily_stats: DailyStats[];
}

export interface AnalyticsOverview {
  total_accounts: number;
  active_accounts: number;
  needs_recovery: number;
  total_emails_sent: number;
  avg_deliverability_score: number;
  accounts_summary: Array<{
    id: number;
    email: string;
    status: AccountStatus;
    score: number;
    sent_today: number;
    target_today: number;
    warming_enabled: boolean;
  }>;
}

export interface AISettings {
  id: number;
  user_id?: number;
  provider: "openai" | "anthropic";
  model: string;
  temperature: number;
  max_tokens: number;
  is_active: boolean;
  has_api_key: boolean;
  updated_at: string;
}

export interface AvailableModel {
  id: string;
  name: string;
  provider: "openai" | "anthropic";
  context_length: number;
  description: string;
}
