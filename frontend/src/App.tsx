import React, { useState } from "react";
import { useWorkspaceStore } from "@/shared/store/useWorkspaceStore";
import { DragDropZone, DocumentGrid, Project } from "@/features/dashboard";
import { DocumentViewer } from "@/features/pdf-viewer";
import { ChatContainer } from "@/features/chat";
import { SettingsDrawer } from "@/features/settings";

const App: React.FC = () => {
  const activeProjectId = useWorkspaceStore((state) => state.activeProjectId);
  const setActiveProjectId = useWorkspaceStore((state) => state.setActiveProjectId);

  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [projects, setProjects] = useState<Project[]>([
    {
      project_id: "p1",
      title: "Quarterly Financial Analysis.pdf",
      description: "Q2 Financial analysis containing balance sheets and projections.",
      created_at: new Date().toISOString(),
      is_archived: false,
    },
    {
      project_id: "p2",
      title: "Llama 3 Technical Report.pdf",
      description: "Core architecture design, parameters, and benchmark tables.",
      created_at: new Date().toISOString(),
      is_archived: false,
    }
  ]);

  const handleUploadAccepted = (file: File) => {
    const newProj: Project = {
      project_id: `p-${Date.now()}`,
      title: file.name,
      description: `Uploaded document: ${file.name}`,
      created_at: new Date().toISOString(),
      is_archived: false,
    };
    setProjects((prev) => [newProj, ...prev]);
    setActiveProjectId(newProj.project_id);
  };

  return (
    <div className="flex flex-col h-screen bg-background text-foreground font-sans">
      {/* Top Navbar Header */}
      <header className="flex items-center justify-between px-6 py-4 border-b border-border bg-card shadow-sm z-10">
        <div className="flex items-center space-x-4">
          <h1 
            onClick={() => setActiveProjectId(null)} 
            className="text-xl font-bold cursor-pointer hover:opacity-90 select-none tracking-tight flex items-center gap-2"
          >
            🧠 CogniDocent
          </h1>
          {activeProjectId && (
            <span className="text-xs bg-primary/10 text-primary font-semibold px-2.5 py-0.5 rounded">
              Active: {projects.find(p => p.project_id === activeProjectId)?.title}
            </span>
          )}
        </div>

        <div className="flex items-center space-x-3">
          {activeProjectId && (
            <button
              type="button"
              onClick={() => setActiveProjectId(null)}
              className="text-sm px-4 py-2 border border-border rounded hover:bg-muted font-medium transition-all"
            >
              Dashboard
            </button>
          )}
          <button
            type="button"
            onClick={() => setIsSettingsOpen(true)}
            className="text-sm px-4 py-2 bg-primary text-primary-foreground font-medium rounded hover:bg-primary/95 transition-all"
          >
            Settings
          </button>
        </div>
      </header>

      {/* Main Container Layout */}
      <main className="flex-1 overflow-hidden">
        {activeProjectId ? (
          // Split-Screen Workspace Viewer
          <div className="flex h-full w-full">
            <div className="w-[55%] h-full">
              <DocumentViewer documentUrl={`/api/v1/documents/${activeProjectId}`} />
            </div>
            <div className="w-[45%] h-full border-l border-border">
              <ChatContainer />
            </div>
          </div>
        ) : (
          // Landing Dashboard
          <div className="max-w-6xl mx-auto px-6 py-8 h-full overflow-y-auto space-y-8">
            <div className="text-center py-6">
              <h2 className="text-4xl font-extrabold tracking-tight mb-2">AI Document Research Assistant</h2>
              <p className="text-muted text-lg max-w-xl mx-auto">
                Upload technical docs, research papers, or manuals to query and navigate source references.
              </p>
            </div>

            <DragDropZone onFileAccepted={handleUploadAccepted} />

            <div className="space-y-4">
              <h3 className="text-lg font-bold">Your Research Documents</h3>
              <DocumentGrid 
                projects={projects} 
                onProjectSelect={setActiveProjectId} 
              />
            </div>
          </div>
        )}
      </main>

      {/* Settings Drawer */}
      <SettingsDrawer 
        isOpen={isSettingsOpen} 
        onClose={() => setIsSettingsOpen(false)} 
      />
    </div>
  );
};

export default App;
