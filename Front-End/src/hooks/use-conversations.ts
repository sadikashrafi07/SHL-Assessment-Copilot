import { useCallback, useEffect, useMemo, useState } from "react";
import type { ChatMessage, Conversation } from "@/types";

const STORAGE_KEY = "shl-copilot:conversations";
const ACTIVE_KEY = "shl-copilot:active";

function uid() {
  return Math.random().toString(36).slice(2, 10) + Date.now().toString(36);
}

function load(): Conversation[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? (JSON.parse(raw) as Conversation[]) : [];
  } catch {
    return [];
  }
}

function persist(list: Conversation[]) {
  if (typeof window === "undefined") return;
  localStorage.setItem(STORAGE_KEY, JSON.stringify(list));
}

export function useConversations() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [hydrated, setHydrated] = useState(false);

  useEffect(() => {
    const list = load();
    setConversations(list);
    const stored = typeof window !== "undefined" ? localStorage.getItem(ACTIVE_KEY) : null;
    if (stored && list.some((c) => c.id === stored)) setActiveId(stored);
    else if (list.length > 0) setActiveId(list[0].id);
    setHydrated(true);
  }, []);

  useEffect(() => {
    if (!hydrated) return;
    persist(conversations);
  }, [conversations, hydrated]);

  useEffect(() => {
    if (!hydrated) return;
    if (activeId) localStorage.setItem(ACTIVE_KEY, activeId);
  }, [activeId, hydrated]);

  const active = useMemo(
    () => conversations.find((c) => c.id === activeId) || null,
    [conversations, activeId],
  );

  const newConversation = useCallback(() => {
    const c: Conversation = {
      id: uid(),
      title: "New chat",
      createdAt: Date.now(),
      updatedAt: Date.now(),
      messages: [],
    };
    setConversations((prev) => [c, ...prev]);
    setActiveId(c.id);
    return c;
  }, []);

  const ensureActive = useCallback((): Conversation => {
    if (active) return active;
    return newConversation();
  }, [active, newConversation]);

  const appendMessage = useCallback(
    (conversationId: string, message: ChatMessage) => {
      setConversations((prev) =>
        prev.map((c) =>
          c.id === conversationId
            ? {
                ...c,
                updatedAt: Date.now(),
                title:
                  c.title === "New chat" && message.role === "user"
                    ? message.content.slice(0, 48)
                    : c.title,
                messages: [...c.messages, message],
              }
            : c,
        ),
      );
    },
    [],
  );

  const updateMessage = useCallback(
    (conversationId: string, messageId: string, patch: Partial<ChatMessage>) => {
      setConversations((prev) =>
        prev.map((c) =>
          c.id === conversationId
            ? {
                ...c,
                messages: c.messages.map((m) => (m.id === messageId ? { ...m, ...patch } : m)),
              }
            : c,
        ),
      );
    },
    [],
  );

  const clearActive = useCallback(() => {
    if (!activeId) return;
    setConversations((prev) =>
      prev.map((c) => (c.id === activeId ? { ...c, messages: [], title: "New chat" } : c)),
    );
  }, [activeId]);

  const deleteConversation = useCallback(
    (id: string) => {
      setConversations((prev) => prev.filter((c) => c.id !== id));
      if (activeId === id) setActiveId(null);
    },
    [activeId],
  );

  return {
    conversations,
    active,
    activeId,
    setActiveId,
    newConversation,
    ensureActive,
    appendMessage,
    updateMessage,
    clearActive,
    deleteConversation,
    hydrated,
  };
}

export { uid };
