import React, { useState } from "react";

interface SettingsDrawerProps {
  isOpen: boolean;
  onClose: () => void;
}

export const SettingsDrawer: React.FC<SettingsDrawerProps> = ({ isOpen, onClose }) => {
  const [openaiKey, setOpenaiKey] = useState("");
  const [geminiKey, setGeminiKey] = useState("");

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    localStorage.setItem("openai_api_key", openaiKey);
    localStorage.setItem("gemini_api_key", geminiKey);
    alert("Settings saved successfully!");
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-black/40">
      <div className="w-96 bg-card text-card-foreground border-l border-border p-6 h-full flex flex-col justify-between shadow-xl">
        <div>
          <div className="flex justify-between items-center mb-6">
            <h3 className="font-semibold text-lg">Provider Settings</h3>
            <button 
              type="button"
              onClick={onClose} 
              className="p-1 hover:bg-muted rounded text-muted hover:text-foreground"
            >
              ✕
            </button>
          </div>

          <form onSubmit={handleSave} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold uppercase mb-1">OpenAI API Key</label>
              <input
                type="password"
                placeholder="sk-..."
                value={openaiKey}
                onChange={(e) => setOpenaiKey(e.target.value)}
                className="w-full border border-border rounded px-3 py-2 bg-background text-foreground text-sm focus:outline-none focus:border-primary"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase mb-1">Gemini API Key</label>
              <input
                type="password"
                placeholder="AIzaSy..."
                value={geminiKey}
                onChange={(e) => setGeminiKey(e.target.value)}
                className="w-full border border-border rounded px-3 py-2 bg-background text-foreground text-sm focus:outline-none focus:border-primary"
              />
            </div>

            <button
              type="submit"
              className="w-full bg-primary text-primary-foreground font-semibold py-2 rounded hover:bg-primary/95 mt-4"
            >
              Save Keys
            </button>
          </form>
        </div>

        <div className="text-center text-xs text-muted">
          Keys are stored locally in your browser.
        </div>
      </div>
    </div>
  );
};
