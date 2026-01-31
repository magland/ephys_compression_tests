import { ComparisonMode } from "../../types/comparison";

interface ComparisonModeSelectorProps {
  mode: ComparisonMode;
  onModeChange: (mode: ComparisonMode) => void;
}

export const ComparisonModeSelector = ({
  mode,
  onModeChange,
}: ComparisonModeSelectorProps) => {
  const modes: { value: ComparisonMode; label: string }[] = [
    { value: "original", label: "Original Only" },
    { value: "overlay", label: "Overlay (Original + Reconstructed)" },
    { value: "residuals", label: "Residuals (Original - Reconstructed)" },
    { value: "side-by-side", label: "Side-by-Side" },
  ];

  return (
    <div style={{ marginBottom: "16px" }}>
      <label
        style={{
          display: "block",
          marginBottom: "8px",
          fontSize: "14px",
          fontWeight: "500",
          color: "#333",
        }}
      >
        View mode:
      </label>
      <div style={{ display: "flex", gap: "12px", flexWrap: "wrap" }}>
        {modes.map((m) => (
          <label
            key={m.value}
            style={{
              display: "flex",
              alignItems: "center",
              cursor: "pointer",
              fontSize: "14px",
            }}
          >
            <input
              type="radio"
              name="comparison-mode"
              value={m.value}
              checked={mode === m.value}
              onChange={() => onModeChange(m.value)}
              style={{ marginRight: "6px" }}
            />
            {m.label}
          </label>
        ))}
      </div>
    </div>
  );
};
