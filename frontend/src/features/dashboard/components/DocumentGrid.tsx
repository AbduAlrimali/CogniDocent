import React from "react";

export interface Project {
  project_id: string;
  title: string;
  description?: string;
  created_at: string;
  is_archived: boolean;
}

interface DocumentGridProps {
  projects: Project[];
  onProjectSelect: (projectId: string) => void;
}

export const DocumentGrid: React.FC<DocumentGridProps> = ({ projects, onProjectSelect }) => {
  if (projects.length === 0) {
    return (
      <div className="text-center p-12 text-muted">
        No projects uploaded yet. Start by dragging a PDF document above.
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {projects.map((project) => (
        <div
          key={project.project_id}
          onClick={() => onProjectSelect(project.project_id)}
          className="border border-border rounded-lg p-6 hover:shadow-md hover:border-primary/50 transition-all cursor-pointer bg-card text-card-foreground"
        >
          <h3 className="font-semibold text-lg mb-2 truncate">{project.title}</h3>
          <p className="text-sm text-muted mb-4 h-10 overflow-hidden line-clamp-2">
            {project.description || "No description provided."}
          </p>
          <div className="flex justify-between items-center text-xs text-muted">
            <span>Created: {new Date(project.created_at).toLocaleDateString()}</span>
            {project.is_archived && (
              <span className="bg-muted px-2 py-0.5 rounded text-foreground">Archived</span>
            )}
          </div>
        </div>
      ))}
    </div>
  );
};
