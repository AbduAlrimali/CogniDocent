import React, { useEffect, useState } from "react";
import { useWorkspaceStore } from "@/shared/store/useWorkspaceStore";
import { Toolbar } from "./Toolbar";

interface DocumentViewerProps {
  documentUrl: string;
}

export const DocumentViewer: React.FC<DocumentViewerProps> = ({ documentUrl }) => {
  const activePage = useWorkspaceStore((state) => state.activePage);
  const totalPages = useWorkspaceStore((state) => state.totalPages);
  const setTotalPages = useWorkspaceStore((state) => state.setTotalPages);
  const setActivePage = useWorkspaceStore((state) => state.setActivePage);
  const [scale, setScale] = useState(1.0);

  useEffect(() => {
    // Simulation placeholder: sets total pages of active document
    setTotalPages(40);
  }, [documentUrl, setTotalPages]);

  const handleNextPage = () => {
    if (activePage < totalPages) {
      setActivePage(activePage + 1);
    }
  };

  const handlePrevPage = () => {
    if (activePage > 1) {
      setActivePage(activePage - 1);
    }
  };

  return (
    <div className="flex flex-col h-full bg-muted border-r border-border">
      <Toolbar
        scale={scale}
        setScale={setScale}
        onNextPage={handleNextPage}
        onPrevPage={handlePrevPage}
      />
      <div className="flex-1 overflow-auto p-6 flex justify-center items-start">
        {/* Render Page Container */}
        <div 
          className="bg-card text-card-foreground shadow-lg border border-border flex flex-col items-center justify-center transition-transform origin-top select-text"
          style={{ 
            width: `${612 * scale}px`, 
            height: `${792 * scale}px`,
          }}
        >
          <div className="text-center p-8 select-none">
            <h4 className="font-semibold text-lg mb-2">PDF Document Viewer</h4>
            <p className="text-sm text-muted">Page {activePage} of {totalPages}</p>
            <p className="text-xs text-muted/60 mt-4">Loaded Document: {documentUrl}</p>
          </div>
        </div>
      </div>
    </div>
  );
};
