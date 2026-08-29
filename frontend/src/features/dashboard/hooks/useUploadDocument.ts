import { useState, useCallback } from "react";

export const useUploadDocument = () => {
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const upload = useCallback(async (file: File) => {
    setIsUploading(true);
    setError(null);
    try {
      const formData = new FormData();
      formData.append("file", file);

      const response = await fetch("/api/v1/projects/upload", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error("Upload failed. Server responded with an error.");
      }

      const data = await response.json();
      return data;
    } catch (err) {
      const errorObj = err instanceof Error ? err : new Error("Unknown upload error");
      setError(errorObj);
      throw errorObj;
    } finally {
      setIsUploading(false);
    }
  }, []);

  return { upload, isUploading, error };
};
