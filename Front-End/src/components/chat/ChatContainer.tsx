import { useEffect, useRef } from "react";
import type { ChatMessage as ChatMessageT, Recommendation } from "@/types";
import { ChatMessage } from "./ChatMessage";
import { TypingIndicator } from "./TypingIndicator";
import { EmptyState } from "./EmptyState";

interface Props {
  messages: ChatMessageT[];
  loading: boolean;
  error: string | null;
  selectedKeys: Set<string>;
  onToggleSelect: (rec: Recommendation, key: string) => void;
  onPickSuggestion: (q: string) => void;
}

export function ChatContainer({
  messages,
  loading,
  error,
  selectedKeys,
  onToggleSelect,
  onPickSuggestion,
}: Props) {
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages, loading]);

  return (
    <div className="flex-1 overflow-y-auto">
      <div className="mx-auto w-full max-w-3xl px-4 py-6">
        {messages.length === 0 && !loading ? (
          <EmptyState onPick={onPickSuggestion} />
        ) : (
          <div className="space-y-6">
            {messages.map((m) => (
              <ChatMessage
                key={m.id}
                message={m}
                selectedKeys={selectedKeys}
                onToggleSelect={onToggleSelect}
              />
            ))}
            {loading && (
              <div className="flex gap-3">
                <div className="h-8 w-8 shrink-0 rounded-xl bg-gradient-to-br from-primary to-primary/70" />
                <TypingIndicator />
              </div>
            )}
            {error && (
              <div className="rounded-2xl border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive">
                {error}
              </div>
            )}
            <div ref={endRef} />
          </div>
        )}
      </div>
    </div>
  );
}
