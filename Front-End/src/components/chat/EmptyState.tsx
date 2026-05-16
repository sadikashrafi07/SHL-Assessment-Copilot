import { motion } from "framer-motion";
import { Sparkles } from "lucide-react";

const SUGGESTIONS = [
  "Senior product manager with strong leadership traits",
  "Entry-level software engineer cognitive screening",
  "Customer service rep — situational judgment test",
  "Sales leader personality and motivation profile",
];

export function EmptyState({ onPick }: { onPick: (q: string) => void }) {
  return (
    <div className="mx-auto flex w-full max-w-2xl flex-col items-center justify-center py-12 text-center">
      <motion.div
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-primary to-primary/70 text-primary-foreground shadow-lg"
      >
        <Sparkles className="h-6 w-6" />
      </motion.div>
      <h1 className="text-2xl font-semibold tracking-tight text-foreground">
        SHL Assessment Copilot
      </h1>
      <p className="mt-2 max-w-md text-sm text-muted-foreground">
        Describe a role, skills, or hiring context. I'll recommend the best-fit SHL assessments with
        confidence scores and rationale.
      </p>

      <div className="mt-8 grid w-full grid-cols-1 gap-2 sm:grid-cols-2">
        {SUGGESTIONS.map((s, i) => (
          <motion.button
            key={s}
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.05 * i }}
            onClick={() => onPick(s)}
            className="rounded-2xl border border-border bg-card p-3 text-left text-xs text-foreground shadow-sm transition-all hover:-translate-y-0.5 hover:border-primary/40 hover:shadow-md"
          >
            {s}
          </motion.button>
        ))}
      </div>
    </div>
  );
}
