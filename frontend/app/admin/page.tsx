"use client";
import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useForm, Controller } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Settings, Key, Brain, Eye, EyeOff, Users, BarChart3, Flame, CheckCircle } from "lucide-react";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { adminApi, getErrorMessage } from "@/lib/api";
import { toast } from "@/components/ui/Toaster";
import { cn } from "@/lib/utils";
import type { AvailableModel } from "@/lib/types";

const aiSchema = z.object({
  provider: z.enum(["openai", "anthropic"]),
  model: z.string().min(1),
  api_key: z.string().optional(),
  temperature: z.coerce.number().min(0).max(2),
  max_tokens: z.coerce.number().int().min(100).max(4000),
});

type AIFormData = z.infer<typeof aiSchema>;

export default function AdminPage() {
  const [showKey, setShowKey] = useState(false);
  const queryClient = useQueryClient();

  const { data: settings, isLoading } = useQuery({
    queryKey: ["ai-settings"],
    queryFn: () => adminApi.getAISettings().then((r) => r.data),
  });

  const { data: models = [] } = useQuery({
    queryKey: ["available-models"],
    queryFn: () => adminApi.getAvailableModels().then((r) => r.data),
  });

  const { data: stats } = useQuery({
    queryKey: ["admin-stats"],
    queryFn: () => adminApi.getStats().then((r) => r.data),
    refetchInterval: 30_000,
  });

  const { data: users = [] } = useQuery({
    queryKey: ["admin-users"],
    queryFn: () => adminApi.getUsers().then((r) => r.data),
    retry: false,
  });

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors, isSubmitting },
  } = useForm<AIFormData>({
    resolver: zodResolver(aiSchema),
    defaultValues: {
      provider: settings?.provider ?? "openai",
      model: settings?.model ?? "gpt-4o-mini",
      temperature: settings?.temperature ?? 0.8,
      max_tokens: settings?.max_tokens ?? 500,
    },
    values: settings
      ? {
          provider: settings.provider,
          model: settings.model,
          api_key: "",
          temperature: settings.temperature,
          max_tokens: settings.max_tokens,
        }
      : undefined,
  });

  const selectedProvider = watch("provider");
  const filteredModels = models.filter(
    (m: AvailableModel) => m.provider === selectedProvider
  );

  const updateMutation = useMutation({
    mutationFn: (data: AIFormData) =>
      adminApi.updateAISettings({
        ...data,
        api_key: data.api_key || undefined,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["ai-settings"] });
      toast("AI settings saved", "success");
    },
    onError: (err) => toast(getErrorMessage(err), "error"),
  });

  return (
    <DashboardLayout>
      <div className="p-6 space-y-6">
        <div>
          <h1 className="text-xl font-semibold">Settings</h1>
          <p className="text-sm text-muted-foreground mt-0.5">
            Configure AI providers and system settings
          </p>
        </div>

        {/* Stats */}
        {stats && (
          <div className="grid grid-cols-3 gap-4">
            <Card>
              <CardContent className="p-5 flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-brand-50 flex items-center justify-center">
                  <Users className="w-5 h-5 text-brand-500" />
                </div>
                <div>
                  <p className="text-2xl font-bold">{stats.total_users}</p>
                  <p className="text-xs text-muted-foreground">Total Users</p>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-5 flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-blue-50 flex items-center justify-center">
                  <BarChart3 className="w-5 h-5 text-blue-500" />
                </div>
                <div>
                  <p className="text-2xl font-bold">{stats.total_accounts}</p>
                  <p className="text-xs text-muted-foreground">Total Accounts</p>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-5 flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-green-50 flex items-center justify-center">
                  <Flame className="w-5 h-5 text-green-500" />
                </div>
                <div>
                  <p className="text-2xl font-bold">{stats.active_accounts}</p>
                  <p className="text-xs text-muted-foreground">Active Warming</p>
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* AI Settings */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Brain className="w-5 h-5 text-brand-500" />
              <CardTitle>AI Email Generation</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="space-y-3">
                <div className="h-10 bg-muted animate-pulse rounded-lg" />
                <div className="h-10 bg-muted animate-pulse rounded-lg" />
              </div>
            ) : (
              <form onSubmit={handleSubmit((d) => updateMutation.mutate(d))} className="space-y-5">
                {/* Provider selection */}
                <div className="space-y-2">
                  <label className="text-sm font-medium">AI Provider</label>
                  <div className="grid grid-cols-2 gap-3">
                    {(["openai", "anthropic"] as const).map((p) => (
                      <button
                        key={p}
                        type="button"
                        onClick={() => {
                          setValue("provider", p);
                          const firstModel = models.find((m: AvailableModel) => m.provider === p);
                          if (firstModel) setValue("model", firstModel.id);
                        }}
                        className={cn(
                          "flex items-center gap-3 p-4 rounded-xl border transition-colors text-left",
                          selectedProvider === p
                            ? "border-brand-500 bg-brand-50"
                            : "border-border hover:bg-muted"
                        )}
                      >
                        <div className={cn(
                          "w-8 h-8 rounded-lg flex items-center justify-center text-sm font-bold",
                          p === "openai" ? "bg-green-100 text-green-700" : "bg-orange-100 text-orange-700"
                        )}>
                          {p === "openai" ? "AI" : "C"}
                        </div>
                        <div>
                          <p className="font-medium capitalize">{p === "openai" ? "OpenAI" : "Anthropic"}</p>
                          <p className="text-xs text-muted-foreground">
                            {p === "openai" ? "GPT-4o, GPT-4o Mini" : "Claude Opus, Sonnet, Haiku"}
                          </p>
                        </div>
                        {selectedProvider === p && (
                          <CheckCircle className="w-4 h-4 text-brand-500 ml-auto" />
                        )}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Model selection */}
                <div className="space-y-2">
                  <label className="text-sm font-medium">Model</label>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                    {filteredModels.map((model: AvailableModel) => (
                      <button
                        key={model.id}
                        type="button"
                        onClick={() => setValue("model", model.id)}
                        className={cn(
                          "flex items-start gap-3 p-3 rounded-lg border text-left transition-colors",
                          watch("model") === model.id
                            ? "border-brand-500 bg-brand-50"
                            : "border-border hover:bg-muted"
                        )}
                      >
                        <div>
                          <p className="text-sm font-medium">{model.name}</p>
                          <p className="text-xs text-muted-foreground">{model.description}</p>
                        </div>
                        {watch("model") === model.id && (
                          <CheckCircle className="w-4 h-4 text-brand-500 ml-auto flex-shrink-0 mt-0.5" />
                        )}
                      </button>
                    ))}
                  </div>
                </div>

                {/* API Key */}
                <div className="relative">
                  <Input
                    label={`${selectedProvider === "openai" ? "OpenAI" : "Anthropic"} API Key`}
                    type={showKey ? "text" : "password"}
                    placeholder={settings?.has_api_key ? "••••••••••• (stored)" : "sk-..."}
                    hint="Leave blank to keep existing key"
                    {...register("api_key")}
                  />
                  <button
                    type="button"
                    onClick={() => setShowKey(!showKey)}
                    className="absolute right-3 top-[30px] text-muted-foreground hover:text-foreground"
                  >
                    {showKey ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>

                {/* Advanced settings */}
                <div className="grid grid-cols-2 gap-4">
                  <Input
                    label="Temperature"
                    type="number"
                    step="0.1"
                    min="0"
                    max="2"
                    hint="Controls creativity (0=precise, 2=creative)"
                    error={errors.temperature?.message}
                    {...register("temperature")}
                  />
                  <Input
                    label="Max Tokens"
                    type="number"
                    hint="Max length of generated email"
                    error={errors.max_tokens?.message}
                    {...register("max_tokens")}
                  />
                </div>

                <div className="flex items-center justify-between pt-2 border-t border-border">
                  {settings?.has_api_key && (
                    <div className="flex items-center gap-2 text-sm text-green-600">
                      <Key className="w-4 h-4" />
                      API key configured
                    </div>
                  )}
                  <Button
                    type="submit"
                    loading={updateMutation.isPending}
                    className="ml-auto"
                  >
                    Save Settings
                  </Button>
                </div>
              </form>
            )}
          </CardContent>
        </Card>

        {/* Users (admin only) */}
        {Array.isArray(users) && users.length > 0 && (
          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <Users className="w-5 h-5 text-brand-500" />
                <CardTitle>Users</CardTitle>
              </div>
            </CardHeader>
            <CardContent className="p-0">
              <table className="w-full">
                <thead>
                  <tr className="bg-muted/50">
                    <th className="text-left py-3 px-4 text-xs font-medium text-muted-foreground">Name</th>
                    <th className="text-left py-3 px-4 text-xs font-medium text-muted-foreground">Email</th>
                    <th className="text-left py-3 px-4 text-xs font-medium text-muted-foreground">Role</th>
                    <th className="text-left py-3 px-4 text-xs font-medium text-muted-foreground">Joined</th>
                  </tr>
                </thead>
                <tbody>
                  {users.map((user: any) => (
                    <tr key={user.id} className="border-t border-border">
                      <td className="py-3 px-4 text-sm font-medium">{user.full_name}</td>
                      <td className="py-3 px-4 text-sm text-muted-foreground">{user.email}</td>
                      <td className="py-3 px-4">
                        <span className={cn(
                          "text-xs px-2 py-0.5 rounded-full border font-medium",
                          user.is_admin
                            ? "bg-purple-100 text-purple-700 border-purple-200"
                            : "bg-gray-100 text-gray-600 border-gray-200"
                        )}>
                          {user.is_admin ? "Admin" : "User"}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-sm text-muted-foreground">
                        {new Date(user.created_at).toLocaleDateString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </CardContent>
          </Card>
        )}
      </div>
    </DashboardLayout>
  );
}
