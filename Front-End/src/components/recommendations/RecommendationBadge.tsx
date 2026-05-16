import { cn } from "@/lib/utils";
import { getTestType, getStrengthStyle } from "@/lib/test-types";

export function TestTypeBadge({ code }: { code: string }) {
  const { label, className } = getTestType(code);
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border px-2.5 py-0.5 text-[10px] font-medium uppercase tracking-wider",
        className,
      )}
    >
      {label}
    </span>
  );
}

export function StrengthBadge({ strength }: { strength?: string }) {
  const { label, className } = getStrengthStyle(strength);
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border px-2.5 py-0.5 text-[10px] font-medium",
        className,
      )}
    >
      {label}
    </span>
  );
}
