import { BenchmarkResult, Dataset } from "../../types";
import { ReconstructedDataInfo } from "../../types/comparison";

interface LossyAlgorithmSelectorProps {
  dataset: Dataset;
  benchmarkResults: BenchmarkResult[];
  selectedAlgorithm: string | null;
  onSelectAlgorithm: (info: ReconstructedDataInfo | null) => void;
}

export const LossyAlgorithmSelector = ({
  dataset,
  benchmarkResults,
  selectedAlgorithm,
  onSelectAlgorithm,
}: LossyAlgorithmSelectorProps) => {
  // Filter for lossy algorithms with results for this dataset
  const lossyResults = benchmarkResults.filter(
    (result) =>
      result.dataset === dataset.name &&
      result.reconstructed_url_raw != null &&
      result.rmse != null
  );

  if (lossyResults.length === 0) {
    return null;
  }

  const handleChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
    const value = event.target.value;
    if (value === "") {
      onSelectAlgorithm(null);
      return;
    }

    const result = lossyResults.find((r) => r.algorithm === value);
    if (result && result.reconstructed_url_raw) {
      onSelectAlgorithm({
        algorithm: result.algorithm,
        rmse: result.rmse || 0,
        max_error: result.max_error || 0,
        reconstructedUrl: result.reconstructed_url_raw,
        datasetUrl: dataset.data_url_raw || "",
        datasetJsonUrl: dataset.data_url_json || "",
      });
    }
  };

  return (
    <div style={{ marginBottom: "16px" }}>
      <label
        htmlFor="lossy-algorithm-select"
        style={{
          display: "block",
          marginBottom: "8px",
          fontSize: "14px",
          fontWeight: "500",
          color: "#333",
        }}
      >
        Compare with lossy reconstruction:
      </label>
      <select
        id="lossy-algorithm-select"
        value={selectedAlgorithm || ""}
        onChange={handleChange}
        style={{
          width: "100%",
          padding: "8px 12px",
          fontSize: "14px",
          borderRadius: "4px",
          border: "1px solid #ccc",
          backgroundColor: "white",
          cursor: "pointer",
        }}
      >
        <option value="">Original data only</option>
        {lossyResults.map((result) => (
          <option key={result.algorithm} value={result.algorithm}>
            {result.algorithm} (RMSE: {result.rmse?.toFixed(3)}, Max Error:{" "}
            {result.max_error?.toFixed(3)}, Ratio:{" "}
            {result.compression_ratio?.toFixed(2)})
          </option>
        ))}
      </select>
    </div>
  );
};
