import { motion } from "framer-motion";
import { Copy, Sparkles, User, Check } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { useState } from "react";
import type { ChatMessage as ChatMessageT, Recommendation } from "@/types";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { RecommendationList } from "@/components/recommendations/RecommendationList";

interface Props {
  message: ChatMessageT;
  selectedKeys: Set<string>;
  onToggleSelect: (rec: Recommendation, key: string) => void;
}

export function ChatMessage({ message, selectedKeys, onToggleSelect }: Props) {
  const isUser = message.role === "user";
  const [copied, setCopied] = useState(false);

  const onCopy = async () => {
    try {
      await navigator.clipboard.writeText(message.content);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      /* noop */
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
      className={cn("flex w-full gap-3", isUser ? "justify-end" : "justify-start")}
    >
      {!isUser && (
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-primary to-primary/70 text-primary-foreground shadow-sm">
          <Sparkles className="h-4 w-4" />
        </div>
      )}

      <div className={cn("flex max-w-[85%] flex-col gap-2", isUser && "items-end")}>
        <div
          className={cn(
            "rounded-2xl px-4 py-3 text-sm leading-relaxed shadow-sm",
            isUser
              ? "bg-primary text-primary-foreground"
              : "bg-card text-card-foreground border border-border",
          )}
        >
          {isUser ? (
            <p className="whitespace-pre-wrap">{message.content}</p>
          ) : (
            <div className="markdown-body">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{message.content}</ReactMarkdown>
            </div>
          )}
        </div>

        {!isUser && message.content && (
          <div className="flex items-center gap-1 pl-1">
            <Button
              size="sm"
              variant="ghost"
              onClick={onCopy}
              className="h-7 gap-1.5 rounded-lg px-2 text-xs text-muted-foreground hover:text-foreground"
            >
              {copied ? <Check className="h-3 w-3" /> : <Copy className="h-3 w-3" />}
              {copied ? "Copied" : "Copy"}
            </Button>
          </div>
        )}

        {!isUser && message.recommendations && message.recommendations.length > 0 && (
          <RecommendationList
            recommendations={message.recommendations}
            selected={selectedKeys}
            onToggle={(key) => {
              const rec = message.recommendations!.find(
                (r, i) => (r.url || `${r.name}-${i}`) === key,
              );
              if (rec) onToggleSelect(rec, key);
            }}
          />
        )}
      </div>

      {isUser && (
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-muted text-muted-foreground">
          <User className="h-4 w-4" />
        </div>
      )}
    </motion.div>
  );
}
