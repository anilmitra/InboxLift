"use client";
import dynamic from "next/dynamic";
import { useMemo } from "react";
import type { EChartsOption } from "echarts";

const ReactECharts = dynamic(() => import("echarts-for-react"), { ssr: false });

interface Props {
  score: number;
  size?: number;
  title?: string;
}

function scoreColor(score: number): string {
  if (score >= 80) return "#22c55e";
  if (score >= 60) return "#f59e0b";
  if (score >= 40) return "#f97316";
  return "#ef4444";
}

export function ScoreGauge({ score, size = 180, title }: Props) {
  const color = scoreColor(score);

  const option: EChartsOption = useMemo(
    () => ({
      animation: true,
      animationDuration: 1000,
      series: [
        {
          type: "gauge",
          startAngle: 220,
          endAngle: -40,
          min: 0,
          max: 100,
          radius: "90%",
          pointer: { show: false },
          progress: {
            show: true,
            width: 12,
            itemStyle: { color },
          },
          axisLine: {
            lineStyle: { width: 12, color: [[1, "#f1f5f9"]] },
          },
          axisTick: { show: false },
          splitLine: { show: false },
          axisLabel: { show: false },
          detail: {
            valueAnimation: true,
            formatter: (val: number) => `{score|${Math.round(val)}}`,
            rich: {
              score: { fontSize: 36, fontWeight: "bold", color },
            },
            offsetCenter: [0, "10%"],
          },
          data: [{ value: score, name: title || "Score" }],
          title: {
            show: !!title,
            offsetCenter: [0, "50%"],
            fontSize: 12,
            color: "#9ca3af",
          },
        },
      ],
    }),
    [score, color, title]
  );

  return (
    <ReactECharts
      option={option}
      style={{ height: `${size}px`, width: `${size}px` }}
      notMerge
    />
  );
}
