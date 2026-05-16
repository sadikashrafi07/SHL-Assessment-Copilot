import { motion } from "framer-motion";
import type { Recommendation } from "@/types";
import { RecommendationCard } from "./RecommendationCard";

interface Props {
  recommendations: Recommendation[];
  selected: Set<string>;
  onToggle: (key: string) => void;
}

export function RecommendationList({ recommendations, selected, onToggle }: Props) {
  if (recommendations.length === 0) return null;
  return (
    <motion.div layout className="mt-4 grid gap-3 md:grid-cols-2">
      {recommendations.map((r, i) => {
        const key = r.url || `${r.name}-${i}`;
        return (
          <RecommendationCard
            key={key}
            rec={r}
            selected={selected.has(key)}
            onToggleSelect={() => onToggle(key)}
          />
        );
      })}
    </motion.div>
  );
}
