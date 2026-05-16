import { useEffect, useMemo, useState } from "react";
import { toast } from "sonner";
import { Sidebar } from "./Sidebar";
import { Header } from "./Header";
import { ChatContainer } from "@/components/chat/ChatContainer";
import { ChatInput } from "@/components/chat/ChatInput";
import { ComparisonModal } from "@/components/comparison/ComparisonModal";
import { useConversations, uid } from "@/hooks/use-conversations";
import { useHealth } from "@/hooks/use-health";
import { api } from "@/services/api";
import type { APIError, ChatMessage, Recommendation } from "@/types";

export function AppLayout() {
  const {
    conversations,
    active,
    activeId,
    setActiveId,
    ensureActive,
    appendMessage,
    clearActive,
    newConversation,
    deleteConversation,
  } = useConversations();

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [selected, setSelected] = useState<Map<string, Recommendation>>(new Map());
  const [compareOpen, setCompareOpen] = useState(false);
  const health = useHealth();

  useEffect(() => {
    const onResize = () => {
      if (typeof window !== "undefined") setSidebarOpen(window.innerWidth >= 768);
    };
    onResize();
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, []);

  // Reset selection when active conversation changes
  useEffect(() => {
    setSelected(new Map());
  }, [activeId]);

  const messages = active?.messages || [];

  const handleSend = async (text: string) => {
    setError(null);
    const conv = ensureActive();
    const userMsg: ChatMessage = {
      id: uid(),
      role: "user",
      content: text,
      createdAt: Date.now(),
    };
    appendMessage(conv.id, userMsg);

    const history = [...conv.messages, userMsg].map((m) => ({
      role: m.role,
      content: m.content,
    }));

    setLoading(true);
    try {
      const res = await api.chat(history);
      const assistantMsg: ChatMessage = {
        id: uid(),
        role: "assistant",
        content: res.reply || "",
        createdAt: Date.now(),
        recommendations: res.recommendations || [],
      };
      appendMessage(conv.id, assistantMsg);
    } catch (e) {
      const err = e as APIError;
      const msg = err?.message || "Failed to reach the assistant.";
      setError(msg);
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  };

  const toggleSelect = (rec: Recommendation, key: string) => {
    setSelected((prev) => {
      const next = new Map(prev);
      if (next.has(key)) next.delete(key);
      else next.set(key, rec);
      return next;
    });
  };

  const selectedKeys = useMemo(() => new Set(selected.keys()), [selected]);
  const compareItems = useMemo(() => Array.from(selected.values()), [selected]);

  return (
    <div className="flex h-screen w-full overflow-hidden bg-background text-foreground">
      <Sidebar
        conversations={conversations}
        activeId={activeId}
        onSelect={(id) => setActiveId(id)}
        onNew={() => {
          newConversation();
          setError(null);
        }}
        onDelete={deleteConversation}
        health={health}
        open={sidebarOpen}
      />

      {sidebarOpen && (
        <div
          className="fixed inset-0 z-30 bg-background/60 backdrop-blur-sm md:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      <div className="flex min-w-0 flex-1 flex-col">
        <Header
          onToggleSidebar={() => setSidebarOpen((v) => !v)}
          onClearChat={() => {
            clearActive();
            setSelected(new Map());
            setError(null);
            toast.success("Chat cleared");
          }}
          onOpenCompare={() => setCompareOpen(true)}
          compareCount={selected.size}
          title={active?.title || "Assessment Copilot"}
        />
        <ChatContainer
          messages={messages}
          loading={loading}
          error={error}
          selectedKeys={selectedKeys}
          onToggleSelect={toggleSelect}
          onPickSuggestion={(q) => handleSend(q)}
        />
        <ChatInput onSend={handleSend} disabled={loading} loading={loading} />
      </div>

      <ComparisonModal open={compareOpen} onOpenChange={setCompareOpen} items={compareItems} />
    </div>
  );
}
