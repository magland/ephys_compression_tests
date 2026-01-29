import { useState, useEffect } from "react";

export const useMarkdownContent = (path: string) => {
  const [content, setContent] = useState<string>("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchContent = async () => {
      try {
        const response = await fetch(path);
        if (!response.ok) {
          throw new Error(
            `Failed to load markdown content: ${response.statusText}`,
          );
        }
        const text = await response.text();
        setContent(text);
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : "Failed to load markdown content",
        );
      }
    };

    fetchContent();
  }, [path]);

  return { content, error };
};
