"use client";
import dynamic from "next/dynamic";
import { useMemo } from "react";
import type { EChartsOption } from "echarts";

const ReactECharts = dynamic(() => import("echarts-for-react"), { ssr: false });

interface Props {
  sent: number;
  target: number;
  size?: number;
}

export function EmailDonut({ sent, target, size = 140 }: Props) {
  const pct = target > 0 ? Math.min((sent / target) * 100, 100) : 0;

  const option: EChartsOption = useMemo(
    () => ({
      animation: true,
      series: [
        {
          type: "pie",
          radius: ["65%", "85%"],
          avoidLabelOverlap: false,
          label: {
            show: true,
            position: "center",
            formatter: () => `{sent|${sent}}\n{lbl|Sent}`,
            rich: {
              sent: { fontSize: 20, fontWeight: "bold", color: "#111827", lineHeight: 26 },
              lbl: { fontSize: 11, color: "#9ca3af", lineHeight: 16 },
            },
          },
          emphasis: { label: { show: true } },
          labelLine: { show: false },
          data: [
            { value: sent, name: "Sent", itemStyle: { color: "#6366f1" } },
            {
              value: Math.max(target - sent, 0),
              name: "Remaining",
              itemStyle: { color: "#f1f5f9" },
            },
          ],
        },
      ],
    }),
    [sent, target]
  );

  return (
    <ReactECharts
      option={option}
      style={{ height: `${size}px`, width: `${size}px` }}
      notMerge
    />
  );
}
