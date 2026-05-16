import { motion } from "framer-motion";
import { useState } from "react";
import { ChevronDown, ExternalLink } from "lucide-react";
import type { Recommendation } from "@/types";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { cn } from "@/lib/utils";
import { TestTypeBadge, StrengthBadge } from "./RecommendationBadge";

interface Props {
  rec: Recommendation;
  selected: boolean;
  onToggleSelect: () => void;
}

export function RecommendationCard({ rec, selected, onToggleSelect }: Props) {
  const [expanded, setExpanded] = useState(false);
  const confidence = typeof rec.confidence === "number" ? rec.confidence : rec.score;
  const confidencePct = confidence != null ? Math.round(Math.max(0, Math.min(1, confidence)) * 100) : null;

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ y: -2 }}
      transition={{ type: "spring", stiffness: 300, damping: 24 }}
      className={cn(
        "group rounded-2xl border border-border bg-card p-4 shadow-sm transition-all hover:shadow-md",
        selected && "border-primary/50 ring-1 ring-primary/30",
      )}
    >
      <div className="flex items-start gap-3">
        <Checkbox
          checked={selected}
          onCheckedChange={onToggleSelect}
          className="mt-1"
          aria-label={`Select ${rec.name} for comparison`}
        />
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="truncate text-sm font-semibold text-foreground">{rec.name}</h3>
            <TestTypeBadge code={rec.test_type} />
            <StrengthBadge strength={rec.recommendation_strength} />
          </div>

          {confidencePct != null && (
            <div className="mt-3">
              <div className="flex items-center justify-between text-[10px] text-muted-foreground">
                <span>Confidence</span>
                <span className="font-medium text-foreground">{confidencePct}%</span>
              </div>
              <div className="mt-1 h-1.5 w-full overflow-hidden rounded-full bg-muted">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${confidencePct}%` }}
                  transition={{ duration: 0.6, ease: "easeOut" }}
                  className="h-full rounded-full bg-gradient-to-r from-primary to-primary/70"
                />
              </div>
            </div>
          )}

          {rec.description && (
            <p
              className={cn(
                "mt-3 text-xs text-muted-foreground",
                !expanded && "line-clamp-2",
              )}
            >
              {rec.description}
            </p>
          )}

          {expanded && rec.explanation && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              className="mt-3 rounded-xl bg-muted/50 p-3 text-xs text-foreground/80"
            >
              <div className="mb-1 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
                Why this fits
              </div>
              {rec.explanation}
            </motion.div>
          )}

          <div className="mt-3 flex items-center gap-2">
            <Button asChild size="sm" variant="outline" className="rounded-xl gap-1.5">
              <a href={rec.url} target="_blank" rel="noopener noreferrer">
                View on SHL
                <ExternalLink className="h-3 w-3" />
              </a>
            </Button>
            {(rec.description || rec.explanation) && (
              <Button
                size="sm"
                variant="ghost"
                onClick={() => setExpanded((v) => !v)}
                className="rounded-xl gap-1.5"
              >
                {expanded ? "Hide" : "Details"}
                <ChevronDown
                  className={cn("h-3.5 w-3.5 transition-transform", expanded && "rotate-180")}
                />
              </Button>
            )}
          </div>
        </div>
      </div>
    </motion.div>
  );
}
