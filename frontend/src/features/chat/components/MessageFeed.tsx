import React from "react";
import { CitationPill } from "./CitationPill";

export interface Message {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  created_at: string;
}

interface MessageFeedProps {
  messages: Message[];
}

export const MessageFeed: React.FC<MessageFeedProps> = ({ messages }) => {
  const parseContent = (content: string) => {
    // Regex matching citation format: [Page X]
    const regex = /\[Page (\d+)\]/g;
    const parts = content.split(regex);
    if (parts.length === 1) return content;

    return parts.map((part, index) => {
      // Every odd element is the captured page number value from the split
      if (index % 2 !== 0) {
        const pageNum = parseInt(part, 10);
        return <CitationPill key={index} pageNumber={pageNum} />;
      }
      return part;
    });
  };

  return (
    <div className="flex flex-col space-y-4">
      {messages.map((msg) => (
        <div
          key={msg.id}
          className={`flex flex-col max-w-[85%] rounded-lg p-3 ${
            msg.role === "user"
              ? "bg-primary text-primary-foreground self-end"
              : "bg-muted text-foreground self-start border border-border"
          }`}
        >
          <div className="text-xs opacity-75 mb-1 font-semibold uppercase tracking-wider">
            {msg.role}
          </div>
          <div className="text-sm whitespace-pre-wrap leading-relaxed select-text">
            {parseContent(msg.content)}
          </div>
        </div>
      ))}
    </div>
  );
};
