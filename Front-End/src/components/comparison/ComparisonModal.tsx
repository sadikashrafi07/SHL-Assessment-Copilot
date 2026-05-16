import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import type { Recommendation } from "@/types";
import { TestTypeBadge, StrengthBadge } from "@/components/recommendations/RecommendationBadge";
import { ExternalLink } from "lucide-react";

interface Props {
  open: boolean;
  onOpenChange: (v: boolean) => void;
  items: Recommendation[];
}

export function ComparisonModal({ open, onOpenChange, items }: Props) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl">
        <DialogHeader>
          <DialogTitle>Compare assessments</DialogTitle>
        </DialogHeader>
        <div className="overflow-x-auto">
          <table className="w-full border-separate border-spacing-0 text-sm">
            <thead>
              <tr className="text-left text-xs text-muted-foreground">
                <th className="px-3 py-2 font-medium">Attribute</th>
                {items.map((it, i) => (
                  <th key={i} className="px-3 py-2 font-medium text-foreground">
                    {it.name}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              <Row label="Type">
                {items.map((it, i) => (
                  <td key={i} className="px-3 py-3 align-top">
                    <TestTypeBadge code={it.test_type} />
                  </td>
                ))}
              </Row>
              <Row label="Strength">
                {items.map((it, i) => (
                  <td key={i} className="px-3 py-3 align-top">
                    <StrengthBadge strength={it.recommendation_strength} />
                  </td>
                ))}
              </Row>
              <Row label="Confidence">
                {items.map((it, i) => {
                  const c = it.confidence ?? it.score;
                  return (
                    <td key={i} className="px-3 py-3 align-top text-foreground">
                      {c != null ? `${Math.round(c * 100)}%` : "—"}
                    </td>
                  );
                })}
              </Row>
              <Row label="Description">
                {items.map((it, i) => (
                  <td key={i} className="px-3 py-3 align-top text-muted-foreground">
                    {it.description || "—"}
                  </td>
                ))}
              </Row>
              <Row label="Explanation">
                {items.map((it, i) => (
                  <td key={i} className="px-3 py-3 align-top text-muted-foreground">
                    {it.explanation || "—"}
                  </td>
                ))}
              </Row>
              <Row label="Link">
                {items.map((it, i) => (
                  <td key={i} className="px-3 py-3 align-top">
                    <a
                      href={it.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1 text-primary hover:underline"
                    >
                      Open <ExternalLink className="h-3 w-3" />
                    </a>
                  </td>
                ))}
              </Row>
            </tbody>
          </table>
        </div>
      </DialogContent>
    </Dialog>
  );
}

function Row({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <tr className="border-t border-border">
      <td className="border-t border-border px-3 py-3 align-top text-xs font-medium uppercase tracking-wider text-muted-foreground">
        {label}
      </td>
      {children}
    </tr>
  );
}
