import React, { useState } from "react";
import { useWorkspaceStore } from "@/shared/store/useWorkspaceStore";
import { MessageFeed } from "./MessageFeed";
import { useStreamingChat } from "../hooks/useStreamingChat";

export const ChatContainer: React.FC = () => {
  const chatScope = useWorkspaceStore((state) => state.chatScope);
  const setChatScope = useWorkspaceStore((state) => state.setChatScope);
  const currentProvider = useWorkspaceStore((state) => state.currentProvider);
  const setCurrentProvider = useWorkspaceStore((state) => state.setCurrentProvider);
  const currentModel = useWorkspaceStore((state) => state.currentModel);
  const setCurrentModel = useWorkspaceStore((state) => state.setCurrentModel);

  const { messages, sendMessage, isStreaming } = useStreamingChat();
  const [input, setInput] = useState("");

  const handleSend = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isStreaming) return;
    sendMessage(input);
    setInput("");
  };

  return (
    <div className="flex flex-col h-full bg-background text-foreground">
      {/* Top Header Panel controls */}
      <div className="flex items-center justify-between p-4 border-b border-border bg-card">
        <div className="flex space-x-2">
          <select 
            value={currentProvider} 
            onChange={(e) => setCurrentProvider(e.target.value)}
            className="border border-border rounded p-1 text-sm bg-background text-foreground focus:outline-none"
          >
            <option value="OLLAMA">Ollama</option>
            <option value="GEMINI">Gemini</option>
            <option value="OPENAI">OpenAI</option>
          </select>
          <select 
            value={currentModel} 
            onChange={(e) => setCurrentModel(e.target.value)}
            className="border border-border rounded p-1 text-sm bg-background text-foreground focus:outline-none"
          >
            <option value="llama3">Llama 3</option>
            <option value="gemini-1.5-pro">Gemini 1.5 Pro</option>
            <option value="gpt-4o">GPT-4o</option>
          </select>
        </div>

        <div className="flex bg-muted rounded p-0.5 text-xs">
          <button 
            type="button"
            onClick={() => setChatScope("entire_document")}
            className={`px-3 py-1 rounded transition-all ${chatScope === "entire_document" ? "bg-card text-foreground shadow-sm" : "text-muted"}`}
          >
            Document
          </button>
          <button 
            type="button"
            onClick={() => setChatScope("current_page")}
            className={`px-3 py-1 rounded transition-all ${chatScope === "current_page" ? "bg-card text-foreground shadow-sm" : "text-muted"}`}
          >
            Page Only
          </button>
        </div>
      </div>

      {/* Message feed stream */}
      <div className="flex-1 overflow-y-auto p-4">
        <MessageFeed messages={messages} />
      </div>

      {/* Message inputs box */}
      <form onSubmit={handleSend} className="p-4 border-t border-border bg-card">
        <div className="flex space-x-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={`Ask a question... (${chatScope === "current_page" ? "current page" : "entire document"})`}
            className="flex-1 border border-border rounded-lg px-4 py-2 bg-background text-foreground focus:outline-none focus:border-primary"
            disabled={isStreaming}
          />
          <button
            type="submit"
            disabled={isStreaming}
            className="bg-primary text-primary-foreground font-medium px-6 py-2 rounded-lg hover:bg-primary/95 disabled:opacity-50"
          >
            Send
          </button>
        </div>
      </form>
    </div>
  );
};
