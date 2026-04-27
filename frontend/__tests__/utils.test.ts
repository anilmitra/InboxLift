import {
  cn,
  getScoreColor,
  getScoreLabel,
  getStatusBadgeVariant,
  getStatusLabel,
  formatNumber,
} from "@/lib/utils";

describe("cn (class names)", () => {
  it("merges class names", () => {
    expect(cn("foo", "bar")).toBe("foo bar");
  });

  it("handles conditional classes", () => {
    expect(cn("base", false && "hidden", "visible")).toBe("base visible");
  });

  it("merges tailwind classes correctly", () => {
    expect(cn("px-2 py-1", "px-4")).toBe("py-1 px-4");
  });
});

describe("getScoreColor", () => {
  it("returns green for high scores", () => {
    expect(getScoreColor(85)).toBe("text-green-500");
    expect(getScoreColor(100)).toBe("text-green-500");
    expect(getScoreColor(80)).toBe("text-green-500");
  });

  it("returns yellow for good scores", () => {
    expect(getScoreColor(70)).toBe("text-yellow-500");
    expect(getScoreColor(60)).toBe("text-yellow-500");
  });

  it("returns orange for fair scores", () => {
    expect(getScoreColor(50)).toBe("text-orange-500");
    expect(getScoreColor(40)).toBe("text-orange-500");
  });

  it("returns red for poor scores", () => {
    expect(getScoreColor(0)).toBe("text-red-500");
    expect(getScoreColor(39)).toBe("text-red-500");
  });
});

describe("getScoreLabel", () => {
  it("labels scores correctly", () => {
    expect(getScoreLabel(0)).toBe("No data");
    expect(getScoreLabel(30)).toBe("Poor");
    expect(getScoreLabel(50)).toBe("Fair");
    expect(getScoreLabel(70)).toBe("Good");
    expect(getScoreLabel(90)).toBe("Excellent");
  });
});

describe("getStatusBadgeVariant", () => {
  it("returns correct classes for each status", () => {
    expect(getStatusBadgeVariant("active")).toContain("green");
    expect(getStatusBadgeVariant("paused")).toContain("yellow");
    expect(getStatusBadgeVariant("needs_recovery")).toContain("red");
    expect(getStatusBadgeVariant("inactive")).toContain("gray");
    expect(getStatusBadgeVariant("error")).toContain("red");
  });
});

describe("getStatusLabel", () => {
  it("returns human-readable labels", () => {
    expect(getStatusLabel("active")).toBe("Active");
    expect(getStatusLabel("needs_recovery")).toBe("Needs Recovery");
    expect(getStatusLabel("paused")).toBe("Paused");
    expect(getStatusLabel("inactive")).toBe("Inactive");
  });
});

describe("formatNumber", () => {
  it("formats numbers correctly", () => {
    expect(formatNumber(0)).toBe("0");
    expect(formatNumber(999)).toBe("999");
    expect(formatNumber(1000)).toBe("1.0K");
    expect(formatNumber(1500)).toBe("1.5K");
    expect(formatNumber(1000000)).toBe("1.0M");
  });
});
