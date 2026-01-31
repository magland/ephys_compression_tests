interface TagFilterProps {
  availableTags: string[];
  selectedTags: string[];
  onTagToggle: (tag: string) => void;
  label: string;
}

export function TagFilter({
  availableTags,
  selectedTags,
  onTagToggle,
  label,
}: TagFilterProps) {
  return (
    <div style={{ marginTop: "1rem" }}>
      <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
        <div
          style={{ fontSize: "0.9rem", color: "#666", whiteSpace: "nowrap" }}
        >
          {label}:
        </div>
        <div style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem" }}>
          {availableTags.map((tag) => (
            <button
              key={tag}
              onClick={() => onTagToggle(tag)}
              style={{
                padding: "4px 8px",
                border: "1px solid #ddd",
                borderRadius: "4px",
                background: selectedTags.includes(tag) ? "#0066cc" : "white",
                color: selectedTags.includes(tag) ? "white" : "#333",
                cursor: "pointer",
                fontSize: "0.8rem",
                transition: "all 0.2s ease",
              }}
            >
              {tag}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
