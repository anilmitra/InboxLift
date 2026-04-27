"use client";
import dynamic from "next/dynamic";
import { useMemo } from "react";
import type { EChartsOption } from "echarts";
import { DailyStats } from "@/lib/types";

const ReactECharts = dynamic(() => import("echarts-for-react"), { ssr: false });

interface Props {
  data: DailyStats[];
  period: "daily" | "weekly" | "monthly";
  height?: number;
}

export function DeliverabilityChart({ data, period, height = 280 }: Props) {
  const option: EChartsOption = useMemo(
    () => ({
      animation: true,
      animationDuration: 600,
      grid: {
        left: 50,
        right: 20,
        top: 20,
        bottom: 40,
        containLabel: false,
      },
      tooltip: {
        trigger: "axis",
        backgroundColor: "rgba(255,255,255,0.95)",
        borderColor: "#e5e7eb",
        borderWidth: 1,
        textStyle: { color: "#111827", fontSize: 12 },
        axisPointer: { type: "cross", crossStyle: { color: "#9ca3af" } },
      },
      legend: {
        bottom: 0,
        textStyle: { fontSize: 11, color: "#6b7280" },
        icon: "circle",
        itemWidth: 8,
        itemHeight: 8,
      },
      xAxis: {
        type: "category",
        data: data.map((d) => {
          const date = new Date(d.date);
          return date.toLocaleDateString("en-US", { month: "short", day: "numeric" });
        }),
        axisLine: { lineStyle: { color: "#e5e7eb" } },
        axisTick: { show: false },
        axisLabel: { color: "#9ca3af", fontSize: 11 },
        splitLine: { show: false },
      },
      yAxis: {
        type: "value",
        name: "Email Count",
        nameTextStyle: { color: "#9ca3af", fontSize: 10 },
        axisLine: { show: false },
        axisTick: { show: false },
        axisLabel: { color: "#9ca3af", fontSize: 11 },
        splitLine: { lineStyle: { color: "#f3f4f6", type: "dashed" } },
        minInterval: 1,
      },
      series: [
        {
          name: "Emails Sent",
          type: "line",
          data: data.map((d) => d.emails_sent),
          smooth: true,
          symbol: "circle",
          symbolSize: 5,
          lineStyle: { width: 2, color: "#6366f1" },
          itemStyle: { color: "#6366f1" },
          areaStyle: {
            color: { type: "linear", x: 0, y: 0, x2: 0, y2: 1,
              colorStops: [
                { offset: 0, color: "rgba(99,102,241,0.15)" },
                { offset: 1, color: "rgba(99,102,241,0)" },
              ],
            },
          },
        },
        {
          name: "Replies",
          type: "line",
          data: data.map((d) => d.replies),
          smooth: true,
          symbol: "circle",
          symbolSize: 5,
          lineStyle: { width: 2, color: "#10b981" },
          itemStyle: { color: "#10b981" },
        },
        {
          name: "Inbox",
          type: "line",
          data: data.map((d) => d.inbox),
          smooth: true,
          symbol: "circle",
          symbolSize: 5,
          lineStyle: { width: 2, color: "#3b82f6" },
          itemStyle: { color: "#3b82f6" },
        },
        {
          name: "Saved from spam",
          type: "line",
          data: data.map((d) => d.spam_rescued),
          smooth: true,
          symbol: "circle",
          symbolSize: 5,
          lineStyle: { width: 2, color: "#f59e0b" },
          itemStyle: { color: "#f59e0b" },
        },
        {
          name: "Other",
          type: "line",
          data: data.map((d) => d.other),
          smooth: true,
          symbol: "circle",
          symbolSize: 5,
          lineStyle: { width: 2, color: "#8b5cf6" },
          itemStyle: { color: "#8b5cf6" },
        },
        {
          name: "Undelivered",
          type: "line",
          data: data.map((d) => d.undelivered),
          smooth: true,
          symbol: "circle",
          symbolSize: 5,
          lineStyle: { width: 2, color: "#94a3b8" },
          itemStyle: { color: "#94a3b8" },
        },
      ],
    }),
    [data]
  );

  return (
    <div className="w-full">
      <ReactECharts
        option={option}
        style={{ height: `${height}px`, width: "100%" }}
        notMerge
        lazyUpdate
      />
    </div>
  );
}
