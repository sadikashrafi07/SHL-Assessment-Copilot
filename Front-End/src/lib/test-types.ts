export const TEST_TYPE_MAP: Record<string, { label: string; className: string }> = {
  K: { label: "Knowledge", className: "bg-blue-500/10 text-blue-600 dark:text-blue-400 border-blue-500/20" },
  P: { label: "Personality", className: "bg-purple-500/10 text-purple-600 dark:text-purple-400 border-purple-500/20" },
  C: { label: "Cognitive", className: "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20" },
  S: { label: "Situational", className: "bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/20" },
  L: { label: "Leadership", className: "bg-rose-500/10 text-rose-600 dark:text-rose-400 border-rose-500/20" },
};

export function getTestType(code: string) {
  const upper = (code || "").toUpperCase();
  return (
    TEST_TYPE_MAP[upper] || {
      label: upper || "Other",
      className: "bg-muted text-muted-foreground border-border",
    }
  );
}

export function getStrengthStyle(strength?: string) {
  switch ((strength || "").toLowerCase()) {
    case "high":
      return { label: "High match", className: "bg-emerald-500/15 text-emerald-700 dark:text-emerald-400 border-emerald-500/30" };
    case "medium":
      return { label: "Medium match", className: "bg-amber-500/15 text-amber-700 dark:text-amber-400 border-amber-500/30" };
    case "low":
      return { label: "Low match", className: "bg-rose-500/15 text-rose-700 dark:text-rose-400 border-rose-500/30" };
    default:
      return { label: strength || "Suggested", className: "bg-muted text-muted-foreground border-border" };
  }
}
