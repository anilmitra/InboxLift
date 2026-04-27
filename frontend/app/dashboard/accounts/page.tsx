"use client";
import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import * as Dialog from "@radix-ui/react-dialog";
import {
  Plus,
  Trash2,
  Play,
  Pause,
  TestTube,
  ChevronDown,
  CheckCircle,
  XCircle,
  Loader2,
  BarChart3,
  X,
} from "lucide-react";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { accountsApi, getErrorMessage } from "@/lib/api";
import { getStatusBadgeVariant, getStatusLabel, cn, getScoreColor } from "@/lib/utils";
import { toast } from "@/components/ui/Toaster";
import type { EmailAccount } from "@/lib/types";
import Link from "next/link";

const PROVIDER_PRESETS: Record<string, Partial<FormData>> = {
  gmail: { smtp_host: "smtp.gmail.com", smtp_port: 587, imap_host: "imap.gmail.com", imap_port: 993 },
  outlook: { smtp_host: "smtp.office365.com", smtp_port: 587, imap_host: "outlook.office365.com", imap_port: 993 },
  yahoo: { smtp_host: "smtp.mail.yahoo.com", smtp_port: 587, imap_host: "imap.mail.yahoo.com", imap_port: 993 },
  custom: {},
};

const schema = z.object({
  email: z.string().email(),
  display_name: z.string().optional(),
  provider: z.enum(["gmail", "outlook", "yahoo", "custom"]),
  smtp_host: z.string().min(1, "SMTP host required"),
  smtp_port: z.coerce.number().int().min(1).max(65535),
  smtp_use_tls: z.boolean(),
  imap_host: z.string().min(1, "IMAP host required"),
  imap_port: z.coerce.number().int().min(1).max(65535),
  imap_use_ssl: z.boolean(),
  username: z.string().min(1),
  password: z.string().min(1),
  daily_warmup_limit: z.coerce.number().int().min(1).max(500),
  ramp_up_days: z.coerce.number().int().min(7).max(90),
});

type FormData = z.infer<typeof schema>;

function AccountCard({
  account,
  onEnable,
  onPause,
  onDelete,
  onTest,
}: {
  account: EmailAccount;
  onEnable: (id: number) => void;
  onPause: (id: number) => void;
  onDelete: (id: number) => void;
  onTest: (id: number) => void;
}) {
  return (
    <Card hover>
      <CardContent className="p-5">
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-center gap-3 min-w-0">
            <div className="w-10 h-10 rounded-full bg-brand-100 flex items-center justify-center text-brand-600 font-semibold flex-shrink-0">
              {account.email[0].toUpperCase()}
            </div>
            <div className="min-w-0">
              <p className="font-medium text-foreground truncate">{account.email}</p>
              <p className="text-xs text-muted-foreground">{account.display_name || account.provider}</p>
            </div>
          </div>
          <span
            className={cn(
              "text-xs px-2.5 py-1 rounded-full border font-medium flex-shrink-0",
              getStatusBadgeVariant(account.status)
            )}
          >
            {getStatusLabel(account.status)}
          </span>
        </div>

        <div className="mt-4 grid grid-cols-3 gap-3 text-center">
          <div className="p-2 bg-muted/50 rounded-lg">
            <p className={cn("text-lg font-bold", getScoreColor(account.deliverability_score))}>
              {Math.round(account.deliverability_score)}
            </p>
            <p className="text-xs text-muted-foreground">Score</p>
          </div>
          <div className="p-2 bg-muted/50 rounded-lg">
            <p className="text-lg font-bold">{account.emails_sent_today}</p>
            <p className="text-xs text-muted-foreground">Today</p>
          </div>
          <div className="p-2 bg-muted/50 rounded-lg">
            <p className="text-lg font-bold">{account.current_warmup_day}</p>
            <p className="text-xs text-muted-foreground">Day</p>
          </div>
        </div>

        {account.last_connection_error && (
          <div className="mt-3 p-2 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-xs text-red-600 truncate">{account.last_connection_error}</p>
          </div>
        )}

        <div className="mt-4 flex items-center gap-2 flex-wrap">
          <Link href={`/dashboard/warmup/${account.id}`}>
            <Button variant="outline" size="sm">
              <BarChart3 className="w-3.5 h-3.5" />
              Report
            </Button>
          </Link>
          <Button variant="outline" size="sm" onClick={() => onTest(account.id)}>
            <TestTube className="w-3.5 h-3.5" />
            Test
          </Button>
          {account.warming_enabled ? (
            <Button variant="outline" size="sm" onClick={() => onPause(account.id)}>
              <Pause className="w-3.5 h-3.5" />
              Pause
            </Button>
          ) : (
            <Button size="sm" onClick={() => onEnable(account.id)}>
              <Play className="w-3.5 h-3.5" />
              Start Warming
            </Button>
          )}
          <Button
            variant="ghost"
            size="icon"
            className="ml-auto text-muted-foreground hover:text-red-500"
            onClick={() => onDelete(account.id)}
          >
            <Trash2 className="w-4 h-4" />
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

export default function AccountsPage() {
  const [showAdd, setShowAdd] = useState(false);
  const queryClient = useQueryClient();

  const { data: accounts = [], isLoading } = useQuery({
    queryKey: ["accounts"],
    queryFn: () => accountsApi.list().then((r) => r.data),
    refetchInterval: 30_000,
  });

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: {
      provider: "gmail",
      smtp_port: 587,
      smtp_use_tls: true,
      imap_port: 993,
      imap_use_ssl: true,
      daily_warmup_limit: 50,
      ramp_up_days: 30,
      ...PROVIDER_PRESETS.gmail,
    },
  });

  const provider = watch("provider");

  const createMutation = useMutation({
    mutationFn: (data: FormData) => accountsApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["accounts"] });
      toast("Account added successfully", "success");
      setShowAdd(false);
      reset();
    },
    onError: (err) => toast(getErrorMessage(err), "error"),
  });

  const enableMutation = useMutation({
    mutationFn: (id: number) => accountsApi.enableWarmup(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["accounts"] });
      toast("Warming started!", "success");
    },
    onError: (err) => toast(getErrorMessage(err), "error"),
  });

  const pauseMutation = useMutation({
    mutationFn: (id: number) => accountsApi.pauseWarmup(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["accounts"] });
      toast("Warming paused", "info");
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => accountsApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["accounts"] });
      toast("Account removed", "info");
    },
  });

  const testMutation = useMutation({
    mutationFn: (id: number) => accountsApi.testConnection(id),
    onSuccess: (res) => {
      const { success, error } = res.data;
      if (success) toast("Connection successful!", "success");
      else toast(`Connection failed: ${error}`, "error");
    },
    onError: (err) => toast(getErrorMessage(err), "error"),
  });

  const handleProviderChange = (p: string) => {
    setValue("provider", p as FormData["provider"]);
    const preset = PROVIDER_PRESETS[p] || {};
    Object.entries(preset).forEach(([k, v]) => setValue(k as keyof FormData, v as any));
  };

  return (
    <DashboardLayout>
      <div className="p-6 space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-semibold">Email Accounts</h1>
            <p className="text-sm text-muted-foreground mt-0.5">
              Manage accounts in your warming pool
            </p>
          </div>
          <Button onClick={() => setShowAdd(true)}>
            <Plus className="w-4 h-4" />
            Add Account
          </Button>
        </div>

        {isLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="h-52 bg-muted animate-pulse rounded-xl" />
            ))}
          </div>
        ) : accounts.length === 0 ? (
          <div className="text-center py-20 text-muted-foreground">
            <div className="w-16 h-16 bg-brand-50 rounded-full flex items-center justify-center mx-auto mb-4">
              <Plus className="w-8 h-8 text-brand-400" />
            </div>
            <p className="font-medium text-lg">No accounts yet</p>
            <p className="text-sm mt-1">Add email accounts to start the warming process</p>
            <Button className="mt-4" onClick={() => setShowAdd(true)}>
              Add your first account
            </Button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            {accounts.map((account: EmailAccount) => (
              <AccountCard
                key={account.id}
                account={account}
                onEnable={(id) => enableMutation.mutate(id)}
                onPause={(id) => pauseMutation.mutate(id)}
                onDelete={(id) => deleteMutation.mutate(id)}
                onTest={(id) => testMutation.mutate(id)}
              />
            ))}
          </div>
        )}
      </div>

      {/* Add Account Dialog */}
      <Dialog.Root open={showAdd} onOpenChange={setShowAdd}>
        <Dialog.Portal>
          <Dialog.Overlay className="fixed inset-0 bg-black/40 z-50" />
          <Dialog.Content className="fixed z-50 left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 bg-white rounded-2xl shadow-xl p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-5">
              <Dialog.Title className="text-lg font-semibold">Add Email Account</Dialog.Title>
              <Dialog.Close asChild>
                <Button variant="ghost" size="icon">
                  <X className="w-4 h-4" />
                </Button>
              </Dialog.Close>
            </div>

            <form onSubmit={handleSubmit((d) => createMutation.mutate(d))} className="space-y-5">
              {/* Provider selection */}
              <div className="space-y-2">
                <label className="text-sm font-medium">Email Provider</label>
                <div className="grid grid-cols-4 gap-2">
                  {(["gmail", "outlook", "yahoo", "custom"] as const).map((p) => (
                    <button
                      key={p}
                      type="button"
                      onClick={() => handleProviderChange(p)}
                      className={cn(
                        "p-3 rounded-lg border text-sm font-medium transition-colors capitalize",
                        provider === p
                          ? "border-brand-500 bg-brand-50 text-brand-600"
                          : "border-border hover:bg-muted"
                      )}
                    >
                      {p}
                    </button>
                  ))}
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <Input
                  label="Email Address"
                  type="email"
                  placeholder="you@example.com"
                  error={errors.email?.message}
                  {...register("email")}
                />
                <Input
                  label="Display Name (optional)"
                  placeholder="My Gmail Account"
                  {...register("display_name")}
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <Input
                  label="Username"
                  placeholder="Usually your email"
                  error={errors.username?.message}
                  {...register("username")}
                />
                <Input
                  label="Password / App Password"
                  type="password"
                  placeholder="••••••••••"
                  error={errors.password?.message}
                  hint="For Gmail/Outlook use an App Password"
                  {...register("password")}
                />
              </div>

              <div className="border border-border rounded-lg p-4 space-y-4">
                <p className="text-sm font-medium text-foreground">SMTP / IMAP Settings</p>
                <div className="grid grid-cols-2 gap-4">
                  <Input
                    label="SMTP Host"
                    placeholder="smtp.example.com"
                    error={errors.smtp_host?.message}
                    {...register("smtp_host")}
                  />
                  <Input
                    label="SMTP Port"
                    type="number"
                    error={errors.smtp_port?.message}
                    {...register("smtp_port")}
                  />
                  <Input
                    label="IMAP Host"
                    placeholder="imap.example.com"
                    error={errors.imap_host?.message}
                    {...register("imap_host")}
                  />
                  <Input
                    label="IMAP Port"
                    type="number"
                    error={errors.imap_port?.message}
                    {...register("imap_port")}
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <Input
                  label="Daily Warmup Limit"
                  type="number"
                  hint="Max emails to send per day"
                  error={errors.daily_warmup_limit?.message}
                  {...register("daily_warmup_limit")}
                />
                <Input
                  label="Ramp-up Period (days)"
                  type="number"
                  hint="Days to reach daily limit"
                  error={errors.ramp_up_days?.message}
                  {...register("ramp_up_days")}
                />
              </div>

              <div className="flex justify-end gap-3">
                <Dialog.Close asChild>
                  <Button type="button" variant="outline">Cancel</Button>
                </Dialog.Close>
                <Button type="submit" loading={createMutation.isPending}>
                  Add Account
                </Button>
              </div>
            </form>
          </Dialog.Content>
        </Dialog.Portal>
      </Dialog.Root>
    </DashboardLayout>
  );
}
