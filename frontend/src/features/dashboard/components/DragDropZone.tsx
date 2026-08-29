import React, { useCallback, useState } from "react";

interface DragDropZoneProps {
  onFileAccepted: (file: File) => void;
}

export const DragDropZone: React.FC<DragDropZoneProps> = ({ onFileAccepted }) => {
  const [isDragActive, setIsDragActive] = useState(false);

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setIsDragActive(true);
    } else if (e.type === "dragleave") {
      setIsDragActive(false);
    }
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      if (file.type === "application/pdf") {
        onFileAccepted(file);
      } else {
        alert("Please upload a valid PDF document.");
      }
    }
  }, [onFileAccepted]);

  const handleFileInput = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      onFileAccepted(e.target.files[0]);
    }
  }, [onFileAccepted]);

  return (
    <div
      onDragEnter={handleDrag}
      onDragOver={handleDrag}
      onDragLeave={handleDrag}
      onDrop={handleDrop}
      className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors cursor-pointer ${
        isDragActive ? "border-primary bg-primary/5" : "border-border hover:border-primary/50"
      }`}
    >
      <input
        type="file"
        id="file-upload"
        accept=".pdf"
        className="hidden"
        onChange={handleFileInput}
      />
      <label htmlFor="file-upload" className="cursor-pointer">
        <div className="flex flex-col items-center justify-center space-y-2">
          <svg className="w-10 h-10 text-muted" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
          </svg>
          <p className="text-sm font-medium text-foreground">Drag and drop your PDF here, or click to browse</p>
          <p className="text-xs text-muted">Only PDF files supported</p>
        </div>
      </label>
    </div>
  );
};
