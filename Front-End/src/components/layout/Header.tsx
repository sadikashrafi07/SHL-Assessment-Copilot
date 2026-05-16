import { Menu, Trash, GitCompare } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ThemeToggle } from "./ThemeToggle";

interface HeaderProps {
  onToggleSidebar: () => void;
  onClearChat: () => void;
  onOpenCompare: () => void;
  compareCount: number;
  title?: string;
}

export function Header({
  onToggleSidebar,
  onClearChat,
  onOpenCompare,
  compareCount,
  title,
}: HeaderProps) {
  return (
    <header className="sticky top-0 z-30 flex h-14 items-center gap-2 border-b border-border bg-background/80 px-3 backdrop-blur-md md:px-6">
      <Button
        variant="ghost"
        size="icon"
        className="rounded-xl md:hidden"
        onClick={onToggleSidebar}
        aria-label="Toggle sidebar"
      >
        <Menu className="h-4 w-4" />
      </Button>
      <div className="flex-1 truncate text-sm font-medium text-foreground">
        {title || "Assessment Copilot"}
      </div>
      <Button
        variant="outline"
        size="sm"
        onClick={onOpenCompare}
        disabled={compareCount < 2}
        className="rounded-xl gap-2"
      >
        <GitCompare className="h-4 w-4" />
        Compare
        {compareCount > 0 && (
          <span className="ml-1 inline-flex h-5 min-w-5 items-center justify-center rounded-full bg-primary px-1.5 text-[10px] font-semibold text-primary-foreground">
            {compareCount}
          </span>
        )}
      </Button>
      <Button
        variant="ghost"
        size="icon"
        onClick={onClearChat}
        className="rounded-xl"
        aria-label="Clear chat"
      >
        <Trash className="h-4 w-4" />
      </Button>
      <ThemeToggle />
    </header>
  );
}
