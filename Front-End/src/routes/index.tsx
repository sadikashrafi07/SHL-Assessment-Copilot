import { createFileRoute } from "@tanstack/react-router";
import { AppLayout } from "@/components/layout/AppLayout";

export const Route = createFileRoute("/")({
  component: Index,
  head: () => ({
    meta: [
      { title: "SHL Assessment Copilot" },
      {
        name: "description",
        content:
          "AI copilot for recruiters — get SHL assessment recommendations from a conversational interface.",
      },
    ],
  }),
});

function Index() {
  return <AppLayout />;
}
