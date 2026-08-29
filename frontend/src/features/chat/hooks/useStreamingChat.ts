import { useState, useCallback } from "react";
import { Message } from "../components/MessageFeed";
import { useWorkspaceStore } from "@/shared/store/useWorkspaceStore";

export const useStreamingChat = () => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "system-1",
      role: "assistant",
      content: "Hello! I am your AI document research assistant. Ask me anything about this file. For example, check out the key findings on [Page 1]!",
      created_at: new Date().toISOString(),
    }
  ]);
  const [isStreaming, setIsStreaming] = useState(false);

  const activePage = useWorkspaceStore((state) => state.activePage);
  const chatScope = useWorkspaceStore((state) => state.chatScope);
  const currentProvider = useWorkspaceStore((state) => state.currentProvider);
  const currentModel = useWorkspaceStore((state) => state.currentModel);

  const sendMessage = useCallback((content: string) => {
    const userMsg: Message = {
      id: crypto.randomUUID(),
      role: "user",
      content,
      created_at: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setIsStreaming(true);

    // Simulated SSE/streaming response containing citations
    setTimeout(() => {
      const assistantMsg: Message = {
        id: crypto.randomUUID(),
        role: "assistant",
        content: `Analyzing your prompt "${content}" via model ${currentModel} (${currentProvider}). Under scope ${chatScope === "current_page" ? `Page ${activePage}` : "Entire Document"}. Key relevant citations located on [Page ${Math.max(1, activePage - 1)}] and [Page ${activePage}].`,
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, assistantMsg]);
      setIsStreaming(false);
    }, 1200);
  }, [activePage, chatScope, currentProvider, currentModel]);

  return { messages, sendMessage, isStreaming };
};
