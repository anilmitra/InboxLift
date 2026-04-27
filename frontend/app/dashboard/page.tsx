"use client";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { RefreshCw, TrendingUp, Users, Activity, AlertTriangle } from "lucide-react";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { analyticsApi, accountsApi } from "@/lib/api";
import { getScoreColor, getStatusBadgeVariant, getStatusLabel, formatRelativeTime } from "@/lib/utils";
import type { EmailAccount } from "@/lib/types";
import Link from "next/link";
import { cn } from "@/lib/utils";

function StatCard({
  title,
  value,
  icon: Icon,
  description,
  trend,
}: {
  title: string;
  value: string | number;
  icon: React.ElementType;
  description?: string;
  trend?: number;
}) {
  return (
    <Card>
      <CardContent className="pt-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-muted-foreground">{title}</p>
            <p className="text-2xl font-bold text-foreground mt-1">{value}</p>
            {description && (
              <p className="text-xs text-muted-foreground mt-1">{description}</p>
            )}
          </div>
          <div className="w-12 h-12 rounded-xl bg-brand-50 flex items-center justify-center">
            <Icon className="w-6 h-6 text-brand-500" />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function AccountRow({ account }: { account: EmailAccount }) {
  return (
    <Link
      href={`/dashboard/warmup/${account.id}`}
      className="flex items-center justify-between py-3 px-4 hover:bg-muted/50 rounded-lg transition-colors group"
    >
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded-full bg-brand-100 flex items-center justify-center text-brand-600 text-xs font-semibold">
          {account.email[0].toUpperCase()}
        </div>
        <div>
          <p className="text-sm font-medium text-foreground group-hover:text-brand-600 transition-colors">
            {account.email}
          </p>
          {account.last_warmup_at && (
            <p className="text-xs text-muted-foreground">
              Last warmed {formatRelativeTime(account.last_warmup_at)}
            </p>
          )}
        </div>
      </div>
      <div className="flex items-center gap-4">
        <div className="text-right">
          <p className="text-xs text-muted-foreground">Today</p>
          <p className="text-sm font-medium">
            {account.emails_sent_today} / {account.target_emails_today}
          </p>
        </div>
        <div className="text-right">
          <p className="text-xs text-muted-foreground">Score</p>
          <p className={cn("text-sm font-bold", getScoreColor(account.deliverability_score))}>
            {Math.round(account.deliverability_score)}
          </p>
        </div>
        <span
          className={cn(
            "text-xs px-2 py-1 rounded-full border font-medium",
            getStatusBadgeVariant(account.status)
          )}
        >
          {getStatusLabel(account.status)}
        </span>
      </div>
    </Link>
  );
}

export default function DashboardPage() {
  const [refreshKey, setRefreshKey] = useState(0);

  const { data: overview, isLoading: overviewLoading } = useQuery({
    queryKey: ["analytics-overview", refreshKey],
    queryFn: () => analyticsApi.overview().then((r) => r.data),
    refetchInterval: 60_000,
  });

  const { data: accounts = [], isLoading: accountsLoading } = useQuery({
    queryKey: ["accounts", refreshKey],
    queryFn: () => accountsApi.list().then((r) => r.data),
    refetchInterval: 60_000,
  });

  const isLoading = overviewLoading || accountsLoading;

  return (
    <DashboardLayout>
      <div className="p-6 space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-semibold text-foreground">Dashboard</h1>
            <p className="text-sm text-muted-foreground">
              Overview of your email warming campaigns
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setRefreshKey((k) => k + 1)}
            >
              <RefreshCw className="w-4 h-4" />
              Refresh
            </Button>
            <Link href="/dashboard/accounts">
              <Button size="sm">Add Account</Button>
            </Link>
          </div>
        </div>

        {/* Stats row */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard
            title="Total Accounts"
            value={overview?.total_accounts ?? "—"}
            icon={Users}
            description="Email accounts monitored"
          />
          <StatCard
            title="Active Warming"
            value={overview?.active_accounts ?? "—"}
            icon={Activity}
            description="Currently sending warm-up emails"
          />
          <StatCard
            title="Total Emails Sent"
            value={overview?.total_emails_sent?.toLocaleString() ?? "—"}
            icon={TrendingUp}
            description="All-time warm-up emails"
          />
          <StatCard
            title="Avg. Score"
            value={
              overview?.avg_deliverability_score != null
                ? `${overview.avg_deliverability_score}/100`
                : "—"
            }
            icon={TrendingUp}
            description="Average deliverability score"
          />
        </div>

        {/* Needs Recovery Alert */}
        {(overview?.needs_recovery ?? 0) > 0 && (
          <div className="flex items-center gap-3 p-4 bg-red-50 border border-red-200 rounded-lg">
            <AlertTriangle className="w-5 h-5 text-red-500 flex-shrink-0" />
            <div>
              <p className="text-sm font-medium text-red-700">
                {overview!.needs_recovery} account(s) need recovery
              </p>
              <p className="text-xs text-red-600 mt-0.5">
                These accounts have been flagged as spam. Check them immediately.
              </p>
            </div>
            <Link href="/dashboard/accounts" className="ml-auto">
              <Button size="sm" variant="destructive">
                View
              </Button>
            </Link>
          </div>
        )}

        {/* Accounts list */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Email Accounts</CardTitle>
              <Link href="/dashboard/accounts">
                <Button variant="ghost" size="sm">
                  View all →
                </Button>
              </Link>
            </div>
          </CardHeader>
          <CardContent className="p-2">
            {isLoading ? (
              <div className="space-y-2 p-2">
                {[...Array(3)].map((_, i) => (
                  <div key={i} className="h-14 bg-muted animate-pulse rounded-lg" />
                ))}
              </div>
            ) : accounts.length === 0 ? (
              <div className="text-center py-12 text-muted-foreground">
                <Activity className="w-10 h-10 mx-auto mb-3 opacity-40" />
                <p className="font-medium">No email accounts yet</p>
                <p className="text-sm mt-1">Add your first email account to start warming</p>
                <Link href="/dashboard/accounts">
                  <Button className="mt-4">Add Email Account</Button>
                </Link>
              </div>
            ) : (
              <div className="divide-y divide-border/50">
                {accounts.map((account: EmailAccount) => (
                  <AccountRow key={account.id} account={account} />
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
}
