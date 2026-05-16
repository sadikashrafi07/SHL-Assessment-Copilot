import { useEffect, useRef, useState, type KeyboardEvent } from "react";
import { ArrowUp, Square } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface ChatInputProps {
  onSend: (value: string) => void;
  disabled?: boolean;
  loading?: boolean;
}

export function ChatInput({ onSend, disabled, loading }: ChatInputProps) {
  const [value, setValue] = useState("");
  const ref = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, 200) + "px";
  }, [value]);

  const submit = () => {
    const v = value.trim();
    if (!v || disabled) return;
    onSend(v);
    setValue("");
  };

  const onKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      submit();
    }
  };

  return (
    <div className="border-t border-border bg-background/80 backdrop-blur-md">
      <div className="mx-auto w-full max-w-3xl px-4 py-4">
        <div
          className={cn(
            "group flex items-end gap-2 rounded-2xl border border-border bg-card p-2 shadow-sm transition-all",
            "focus-within:border-primary/50 focus-within:shadow-md",
          )}
        >
          <textarea
            ref={ref}
            value={value}
            onChange={(e) => setValue(e.target.value)}
            onKeyDown={onKeyDown}
            disabled={disabled}
            rows={1}
            placeholder="Describe a role, skills, or context… (Shift+Enter for newline)"
            className="flex-1 resize-none bg-transparent px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none disabled:opacity-50"
          />
          <Button
            size="icon"
            onClick={submit}
            disabled={disabled || !value.trim()}
            className="h-9 w-9 shrink-0 rounded-xl"
            aria-label="Send message"
          >
            {loading ? <Square className="h-4 w-4" /> : <ArrowUp className="h-4 w-4" />}
          </Button>
        </div>
        <div className="mt-2 text-center text-[10px] text-muted-foreground">
          SHL Copilot can make mistakes. Verify assessment fit before use.
        </div>
      </div>
    </div>
  );
}
