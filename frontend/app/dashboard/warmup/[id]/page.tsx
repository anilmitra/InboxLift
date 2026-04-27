"use client";
import { useState, use } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import {
  ArrowLeft,
  Download,
  Settings,
  Play,
  Pause,
  RefreshCw,
  Inbox,
  ShieldCheck,
  Layers,
  XCircle,
  MessageSquare,
  Mail,
} from "lucide-react";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { DeliverabilityChart } from "@/components/charts/DeliverabilityChart";
import { ScoreGauge } from "@/components/charts/ScoreGauge";
import { EmailDonut } from "@/components/charts/EmailDonut";
import { analyticsApi, accountsApi } from "@/lib/api";
import { getStatusBadgeVariant, getStatusLabel, cn } from "@/lib/utils";
import { toast } from "@/components/ui/Toaster";
import type { ESPStats } from "@/lib/types";

type PeriodTab = "daily" | "weekly" | "monthly";

function PlacementCard({
  icon: Icon,
  label,
  value,
  description,
  color,
}: {
  icon: React.ElementType;
  label: string;
  value: number;
  description: string;
  color: string;
}) {
  return (
    <div className="flex items-start gap-3 p-4">
      <div className={cn("w-10 h-10 rounded-lg flex items-center justify-center", color)}>
        <Icon className="w-5 h-5" />
      </div>
      <div>
        <p className="text-xl font-bold text-foreground">{value}</p>
        <p className="text-sm font-medium text-foreground">{label}</p>
        <p className="text-xs text-muted-foreground mt-0.5">{description}</p>
      </div>
    </div>
  );
}

function ESPRow({ stat }: { stat: ESPStats }) {
  const espLabel = stat.esp === "google" ? "Google" : stat.esp === "microsoft" ? "Microsoft" : "Others";
  const espIcon =
    stat.esp === "google" ? "🇬" : stat.esp === "microsoft" ? "🇲" : "📧";

  return (
    <tr className="border-t border-border hover:bg-muted/30 transition-colors">
      <td className="py-3 px-4 text-sm font-medium">
        <div className="flex items-center gap-2">
          {espLabel === "Google" && (
            <svg className="w-4 h-4" viewBox="0 0 24 24"><path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/><path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/><path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/><path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/></svg>
          )}
          {espLabel === "Microsoft" && (
            <svg className="w-4 h-4" viewBox="0 0 24 24"><rect x="1" y="1" width="10" height="10" fill="#F25022"/><rect x="13" y="1" width="10" height="10" fill="#7FBA00"/><rect x="1" y="13" width="10" height="10" fill="#00A4EF"/><rect x="13" y="13" width="10" height="10" fill="#FFB900"/></svg>
          )}
          {espLabel === "Others" && <span className="w-4 h-4 flex items-center justify-center text-xs">📧</span>}
          {espLabel}
        </div>
      </td>
      <td className="py-3 px-4 text-sm text-center">{stat.total_sent}</td>
      <td className="py-3 px-4 text-sm text-center">{stat.replies}</td>
      <td className="py-3 px-4 text-sm text-center">{stat.inbox}</td>
      <td className="py-3 px-4 text-sm text-center">{stat.spam}</td>
      <td className="py-3 px-4 text-sm text-center">{stat.other}</td>
      <td className="py-3 px-4 text-sm text-center">{stat.undelivered}</td>
      <td className="py-3 px-4 text-sm text-center font-medium">
        {stat.deliverability_rate.toFixed(1)}%
      </td>
    </tr>
  );
}

export default function WarmupReportPage({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = use(params);
  const accountId = parseInt(resolvedParams.id);
  const [period, setPeriod] = useState<PeriodTab>("daily");
  const [days, setDays] = useState(7);
  const queryClient = useQueryClient();

  const periodDays = period === "daily" ? 7 : period === "weekly" ? 30 : 90;

  const { data: account } = useQuery({
    queryKey: ["account", accountId],
    queryFn: () => accountsApi.get(accountId).then((r) => r.data),
  });

  const { data: report, isLoading } = useQuery({
    queryKey: ["account-report", accountId, periodDays],
    queryFn: () => analyticsApi.accountReport(accountId, periodDays).then((r) => r.data),
    refetchInterval: 30_000,
  });

  const pauseMutation = useMutation({
    mutationFn: () => accountsApi.pauseWarmup(accountId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["account", accountId] });
      toast("Warming paused", "success");
    },
  });

  const resumeMutation = useMutation({
    mutationFn: () => accountsApi.resumeWarmup(accountId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["account", accountId] });
      toast("Warming resumed", "success");
    },
  });

  return (
    <DashboardLayout>
      <div className="p-6 space-y-5">
        {/* Header */}
        <div className="flex items-center justify-between flex-wrap gap-3">
          <div className="flex items-center gap-3">
            <Link href="/dashboard">
              <Button variant="ghost" size="sm">
                <ArrowLeft className="w-4 h-4" />
                Back
              </Button>
            </Link>
            <div className="flex items-center gap-2">
              <div className="w-5 h-5 rounded bg-brand-100 flex items-center justify-center">
                <span className="text-xs font-semibold text-brand-600">
                  {account?.email?.[0]?.toUpperCase() || "?"}
                </span>
              </div>
              <span className="font-medium text-foreground">{account?.email}</span>
              {account && (
                <span
                  className={cn(
                    "text-xs px-2 py-0.5 rounded-full border font-medium",
                    getStatusBadgeVariant(account.status)
                  )}
                >
                  {getStatusLabel(account.status)}
                </span>
              )}
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Link href={`/dashboard/accounts?edit=${accountId}`}>
              <Button variant="outline" size="sm">
                <Settings className="w-4 h-4" />
                Settings
              </Button>
            </Link>
            {account?.warming_enabled ? (
              <Button
                variant="outline"
                size="sm"
                loading={pauseMutation.isPending}
                onClick={() => pauseMutation.mutate()}
              >
                <Pause className="w-4 h-4" />
                Pause
              </Button>
            ) : (
              <Button
                size="sm"
                loading={resumeMutation.isPending}
                onClick={() => resumeMutation.mutate()}
              >
                <Play className="w-4 h-4" />
                Resume
              </Button>
            )}
          </div>
        </div>

        {/* Chart area */}
        <div className="grid grid-cols-1 xl:grid-cols-4 gap-5">
          {/* Main chart */}
          <Card className="xl:col-span-3">
            <CardHeader>
              <div className="flex items-center justify-between flex-wrap gap-3">
                <CardTitle>Deliverability Analytics</CardTitle>
                <div className="flex items-center gap-2">
                  <div className="flex items-center bg-muted rounded-lg p-1">
                    {(["daily", "weekly", "monthly"] as PeriodTab[]).map((p) => (
                      <button
                        key={p}
                        onClick={() => setPeriod(p)}
                        className={cn(
                          "px-3 py-1.5 text-sm rounded-md font-medium transition-colors",
                          period === p
                            ? "bg-white text-brand-600 shadow-sm"
                            : "text-muted-foreground hover:text-foreground"
                        )}
                      >
                        {p.charAt(0).toUpperCase() + p.slice(1)}
                      </button>
                    ))}
                  </div>
                  <Button variant="outline" size="icon">
                    <Download className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              {isLoading ? (
                <div className="h-64 bg-muted animate-pulse rounded-lg" />
              ) : report?.daily_stats ? (
                <DeliverabilityChart
                  data={report.daily_stats}
                  period={period}
                  height={260}
                />
              ) : null}
            </CardContent>
          </Card>

          {/* Score gauge */}
          <Card>
            <CardHeader>
              <CardTitle className="text-center">Deliverability Score</CardTitle>
            </CardHeader>
            <CardContent className="flex flex-col items-center gap-4">
              <ScoreGauge score={report?.deliverability_score ?? 0} size={180} />
              <div className="w-full space-y-2">
                {[
                  { label: "Google", score: report?.google_score ?? 0 },
                  { label: "Microsoft", score: report?.microsoft_score ?? 0 },
                  { label: "Others", score: report?.others_score ?? 0 },
                ].map(({ label, score }) => (
                  <div key={label} className="flex items-center justify-between text-sm">
                    <span className="text-muted-foreground">{label}</span>
                    <div className="flex items-center gap-2">
                      <div className="w-20 h-1.5 bg-muted rounded-full overflow-hidden">
                        <div
                          className="h-full bg-brand-500 rounded-full"
                          style={{ width: `${score}%` }}
                        />
                      </div>
                      <span className="font-medium w-12 text-right">
                        {Math.round(score)}/100
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Stats row */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <Card>
            <CardContent className="p-5">
              <div className="flex items-center gap-3">
                <EmailDonut
                  sent={account?.emails_sent_today ?? 0}
                  target={account?.target_emails_today ?? 1}
                  size={80}
                />
                <div>
                  <p className="text-xs text-muted-foreground">Total Sent</p>
                  <p className="text-xl font-bold">{report?.total_sent ?? 0}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Received */}
          <Card>
            <CardContent className="p-5 flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-blue-50 flex items-center justify-center">
                <Mail className="w-5 h-5 text-blue-500" />
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Received</p>
                <p className="text-xl font-bold">{report?.total_received ?? 0}</p>
                <p className="text-xs text-muted-foreground">From warm-up accounts</p>
              </div>
            </CardContent>
          </Card>

          {/* Replies */}
          <Card>
            <CardContent className="p-5 flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-green-50 flex items-center justify-center">
                <MessageSquare className="w-5 h-5 text-green-500" />
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Replies</p>
                <p className="text-xl font-bold">{report?.total_replies ?? 0}</p>
                <p className="text-xs text-muted-foreground">Responses sent</p>
              </div>
            </CardContent>
          </Card>

          {/* Warmup Day */}
          <Card>
            <CardContent className="p-5 flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-orange-50 flex items-center justify-center">
                <RefreshCw className="w-5 h-5 text-brand-500" />
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Warmup Day</p>
                <p className="text-xl font-bold">{account?.current_warmup_day ?? 0}</p>
                <p className="text-xs text-muted-foreground">
                  of {account?.ramp_up_days ?? 30}
                </p>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Placement Breakdown */}
        <Card>
          <CardHeader>
            <CardTitle>Placement Breakdown</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 lg:grid-cols-4 divide-x divide-border">
              <PlacementCard
                icon={Inbox}
                label="Inbox"
                value={report?.placement.inbox ?? 0}
                description="Reached primary inbox directly"
                color="bg-green-50 text-green-600"
              />
              <PlacementCard
                icon={ShieldCheck}
                label="Saved from spam"
                value={report?.placement.spam_rescued ?? 0}
                description="Detected in spam & moved to inbox"
                color="bg-orange-50 text-orange-600"
              />
              <PlacementCard
                icon={Layers}
                label="Others"
                value={report?.placement.other ?? 0}
                description="Promotions, social & other tabs"
                color="bg-purple-50 text-purple-600"
              />
              <PlacementCard
                icon={XCircle}
                label="Undelivered"
                value={report?.placement.undelivered ?? 0}
                description="Failed to reach recipient"
                color="bg-gray-100 text-gray-500"
              />
            </div>
          </CardContent>
        </Card>

        {/* ESP Performance Table */}
        <Card>
          <CardHeader>
            <CardTitle>ESP Based Performance</CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="bg-muted/50">
                    <th className="text-left py-3 px-4 text-xs font-medium text-muted-foreground">
                      Recipient&apos;s ESP
                    </th>
                    <th className="text-center py-3 px-4 text-xs font-medium text-muted-foreground">
                      Total Sent
                    </th>
                    <th className="text-center py-3 px-4 text-xs font-medium text-muted-foreground">
                      Replies
                    </th>
                    <th className="text-center py-3 px-4 text-xs font-medium text-muted-foreground">
                      Inbox
                    </th>
                    <th className="text-center py-3 px-4 text-xs font-medium text-muted-foreground">
                      Saved from spam
                    </th>
                    <th className="text-center py-3 px-4 text-xs font-medium text-muted-foreground">
                      Other
                    </th>
                    <th className="text-center py-3 px-4 text-xs font-medium text-muted-foreground">
                      Undelivered
                    </th>
                    <th className="text-center py-3 px-4 text-xs font-medium text-muted-foreground">
                      Deliverability Rate
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {report?.esp_stats.map((stat) => (
                    <ESPRow key={stat.esp} stat={stat} />
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
}
