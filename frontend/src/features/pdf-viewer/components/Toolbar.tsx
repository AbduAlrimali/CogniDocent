import React from "react";
import { useWorkspaceStore } from "@/shared/store/useWorkspaceStore";

interface ToolbarProps {
  scale: number;
  setScale: (scale: number) => void;
  onNextPage: () => void;
  onPrevPage: () => void;
}

export const Toolbar: React.FC<ToolbarProps> = ({ scale, setScale, onNextPage, onPrevPage }) => {
  const activePage = useWorkspaceStore((state) => state.activePage);
  const totalPages = useWorkspaceStore((state) => state.totalPages);
  const jumpToPage = useWorkspaceStore((state) => state.jumpToPage);

  const handlePageInput = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      const val = parseInt(e.currentTarget.value, 10);
      if (!isNaN(val)) {
        jumpToPage(val);
      }
    }
  };

  return (
    <div className="flex items-center justify-between px-4 py-2 border-b border-border bg-card text-card-foreground select-none">
      <div className="flex items-center space-x-2">
        <button
          onClick={onPrevPage}
          disabled={activePage <= 1}
          className="p-1 rounded hover:bg-muted disabled:opacity-50"
        >
          &larr;
        </button>
        <div className="flex items-center space-x-1 text-sm">
          <input
            type="text"
            key={activePage}
            defaultValue={activePage}
            onKeyDown={handlePageInput}
            className="w-10 text-center border border-border rounded p-0.5 bg-background text-foreground"
          />
          <span className="text-muted">/ {totalPages}</span>
        </div>
        <button
          onClick={onNextPage}
          disabled={activePage >= totalPages}
          className="p-1 rounded hover:bg-muted disabled:opacity-50"
        >
          &rarr;
        </button>
      </div>

      <div className="flex items-center space-x-2 text-sm">
        <button
          onClick={() => setScale(Math.max(0.5, scale - 0.1))}
          className="px-2 py-1 border border-border rounded hover:bg-muted"
        >
          -
        </button>
        <span>{Math.round(scale * 100)}%</span>
        <button
          onClick={() => setScale(Math.min(2.0, scale + 0.1))}
          className="px-2 py-1 border border-border rounded hover:bg-muted"
        >
          +
        </button>
      </div>
    </div>
  );
};
