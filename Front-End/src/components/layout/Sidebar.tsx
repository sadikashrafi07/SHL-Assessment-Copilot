import { motion, AnimatePresence } from "framer-motion";
import { MessageSquarePlus, Sparkles, Trash2, Activity } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import type { Conversation } from "@/types";

interface SidebarProps {
  conversations: Conversation[];
  activeId: string | null;
  onSelect: (id: string) => void;
  onNew: () => void;
  onDelete: (id: string) => void;
  health: "checking" | "online" | "offline";
  open: boolean;
}

export function Sidebar({
  conversations,
  activeId,
  onSelect,
  onNew,
  onDelete,
  health,
  open,
}: SidebarProps) {
  const healthColor =
    health === "online"
      ? "bg-emerald-500"
      : health === "offline"
        ? "bg-rose-500"
        : "bg-amber-500";
  const healthLabel =
    health === "online" ? "Backend online" : health === "offline" ? "Backend offline" : "Checking…";

  return (
    <AnimatePresence initial={false}>
      {open && (
        <motion.aside
          initial={{ x: -280, opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          exit={{ x: -280, opacity: 0 }}
          transition={{ type: "spring", stiffness: 280, damping: 30 }}
          className="fixed inset-y-0 left-0 z-40 flex w-72 flex-col border-r border-border bg-sidebar/95 backdrop-blur md:relative md:translate-x-0"
        >
          <div className="flex items-center gap-2 px-4 py-4">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-primary to-primary/70 text-primary-foreground shadow-sm">
              <Sparkles className="h-4 w-4" />
            </div>
            <div className="flex flex-col">
              <span className="text-sm font-semibold text-sidebar-foreground">SHL Copilot</span>
              <span className="text-[10px] uppercase tracking-wider text-muted-foreground">
                Assessment AI
              </span>
            </div>
          </div>

          <div className="px-3">
            <Button
              onClick={onNew}
              className="w-full justify-start gap-2 rounded-xl"
              variant="default"
            >
              <MessageSquarePlus className="h-4 w-4" />
              New chat
            </Button>
          </div>

          <div className="mt-4 px-3 text-[10px] font-medium uppercase tracking-wider text-muted-foreground">
            History
          </div>
          <nav className="mt-1 flex-1 space-y-1 overflow-y-auto px-2 pb-4">
            {conversations.length === 0 && (
              <div className="px-3 py-6 text-xs text-muted-foreground">
                No conversations yet. Start by describing a role.
              </div>
            )}
            {conversations.map((c) => (
              <div
                key={c.id}
                className={cn(
                  "group flex items-center gap-1 rounded-xl px-2 py-1.5 transition-colors",
                  activeId === c.id
                    ? "bg-sidebar-accent text-sidebar-accent-foreground"
                    : "hover:bg-sidebar-accent/60",
                )}
              >
                <button
                  onClick={() => onSelect(c.id)}
                  className="flex-1 truncate text-left text-sm"
                  title={c.title}
                >
                  {c.title || "New chat"}
                </button>
                <button
                  onClick={() => onDelete(c.id)}
                  className="rounded-md p-1 opacity-0 transition-opacity hover:bg-destructive/10 hover:text-destructive group-hover:opacity-100"
                  aria-label="Delete conversation"
                >
                  <Trash2 className="h-3.5 w-3.5" />
                </button>
              </div>
            ))}
          </nav>

          <div className="border-t border-sidebar-border px-4 py-3">
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              <Activity className="h-3.5 w-3.5" />
              <span className="flex items-center gap-2">
                <span className={cn("h-2 w-2 rounded-full", healthColor)} />
                {healthLabel}
              </span>
            </div>
          </div>
        </motion.aside>
      )}
    </AnimatePresence>
  );
}
