import { useState, useEffect } from "react";

interface Post {
  path: string;
  content: string;
  date: Date;
}

export const useMarkdownPosts = (directory: string) => {
  const [posts, setPosts] = useState<Post[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchPosts = async () => {
      try {
        // First fetch the index
        const indexResponse = await fetch(`${directory}/index.txt`);
        if (!indexResponse.ok) {
          throw new Error(
            `Failed to load post index: ${indexResponse.statusText}`,
          );
        }
        const indexContent = await indexResponse.text();
        const paths = indexContent.trim().split("\n");

        // Then fetch all posts in parallel
        const postPromises = paths.map(async (path) => {
          const response = await fetch(`${directory}/${path}`);
          if (!response.ok) {
            throw new Error(
              `Failed to load post ${path}: ${response.statusText}`,
            );
          }
          const content = await response.text();

          // Parse date from filename (format: YYYY-MM-DD-title.md)
          const dateMatch = path.match(/^(\d{4}-\d{2}-\d{2})/);
          if (!dateMatch) {
            throw new Error(`Invalid post filename format: ${path}`);
          }
          const date = new Date(dateMatch[1]);

          return { path, content, date };
        });

        const loadedPosts = await Promise.all(postPromises);
        // Sort posts by date, newest first
        loadedPosts.sort((a, b) => b.date.getTime() - a.date.getTime());
        setPosts(loadedPosts);
        setLoading(false);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load posts");
        setLoading(false);
      }
    };

    fetchPosts();
  }, [directory]);

  return { posts, error, loading };
};
