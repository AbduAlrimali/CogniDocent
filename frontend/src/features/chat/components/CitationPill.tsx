import React from "react";
import { useWorkspaceStore } from "@/shared/store/useWorkspaceStore";

interface CitationPillProps {
  pageNumber: number;
}

export const CitationPill: React.FC<CitationPillProps> = ({ pageNumber }) => {
  const jumpToPage = useWorkspaceStore((state) => state.jumpToPage);

  const handleClick = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    jumpToPage(pageNumber);
  };

  return (
    <button
      type="button"
      onClick={handleClick}
      className="inline-flex items-center justify-center px-2 py-0.5 mx-1 text-xs font-semibold rounded bg-primary/10 text-primary hover:bg-primary/20 transition-all border border-primary/20 cursor-pointer"
      title={`Jump to Page ${pageNumber}`}
    >
      Page {pageNumber}
    </button>
  );
};
