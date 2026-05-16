import { useEffect, useState } from "react";
import { api } from "@/services/api";

export function useHealth(intervalMs = 20_000) {
  const [status, setStatus] = useState<"checking" | "online" | "offline">("checking");

  useEffect(() => {
    let mounted = true;
    const ping = async () => {
      const { ok } = await api.health();
      if (mounted) setStatus(ok ? "online" : "offline");
    };
    ping();
    const t = setInterval(ping, intervalMs);
    return () => {
      mounted = false;
      clearInterval(t);
    };
  }, [intervalMs]);

  return status;
}
