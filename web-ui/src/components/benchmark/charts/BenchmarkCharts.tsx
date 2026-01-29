import { useState } from "react";
import Plot from "react-plotly.js";

interface BenchmarkBarChartProps {
  title: string;
  data: ChartData[];
  dataKey: keyof Pick<
    ChartData,
    "compression_ratio" | "encode_speed" | "decode_speed"
  >;
  color: string;
  xAxisTitle: string;
  normalize?: boolean;
}

function BenchmarkBarChart({
  title,
  data,
  dataKey,
  color,
  xAxisTitle,
  normalize,
}: BenchmarkBarChartProps) {
  const normalizedData =
    normalize && dataKey === "compression_ratio"
      ? data.map((d) => ({
          ...d,
          compression_ratio: d.reference_compression_ratio
            ? d.compression_ratio / d.reference_compression_ratio
            : d.compression_ratio,
          reference_compression_ratio: d.reference_compression_ratio ? 1 : null,
        }))
      : data;

  return (
    <div style={{ margin: "0 20px 20px 0" }}>
      <h3 style={{ marginBottom: "10px" }}>{title}</h3>
      <Plot
        data={[
          {
            type: "bar",
            orientation: "h",
            y: normalizedData.map((d) => d.algorithmOrDataset),
            x: normalizedData.map((d) => d[dataKey]),
            marker: { color },
            name: title,
            hovertemplate:
              normalize && dataKey === "compression_ratio"
                ? "%{x:.3f}×<extra></extra>"
                : "%{x:.2f}<extra></extra>",
          },
          ...(dataKey === "compression_ratio" &&
          normalizedData.some((d) => d.reference_compression_ratio !== null)
            ? [
                ...normalizedData
                  .filter((d) => d.reference_compression_ratio !== null)
                  .flatMap((d) => [
                    {
                      type: "scatter" as const,
                      mode: "lines" as const,
                      y: [d.algorithmOrDataset, d.algorithmOrDataset],
                      x: [0, d.reference_compression_ratio],
                      line: { color, width: 1 },
                      showlegend: false,
                      hoverinfo: "skip" as const,
                    },
                    {
                      type: "scatter" as const,
                      mode: "markers" as const,
                      y: [d.algorithmOrDataset],
                      x: [d.reference_compression_ratio],
                      marker: { color: "#aaaaaa", size: 8 },
                      name: "Best Compression",
                      hovertemplate: normalize
                        ? "Best: 1.000×<extra></extra>"
                        : "Best: %{x:.2f}<extra></extra>",
                      showlegend:
                        d.algorithmOrDataset ===
                        normalizedData[0].algorithmOrDataset,
                    },
                  ]),
              ]
            : []),
        ]}
        layout={{
          width: 700,
          height: Math.max(300, data.length * 23 + 40),
          margin: { t: 5, r: 30, l: 200, b: 30 },
          xaxis: { title: xAxisTitle },
          yaxis: { automargin: true, ticksuffix: "  " },
          dragmode: false,
        }}
        config={{ displayModeBar: false }}
      />
    </div>
  );
}

interface ChartData {
  algorithmOrDataset: string;
  compression_ratio: number;
  reference_compression_ratio: number | null; // the highest compression ratio for the dataset (if algorithmOrDataset is a dataset)
  encode_speed: number;
  decode_speed: number;
}

interface BenchmarkChartsProps {
  chartData: ChartData[];
  showSortByCompressionRatio?: boolean;
  showNormalizeByReference?: boolean;
}

export function BenchmarkCharts({
  chartData,
  showSortByCompressionRatio,
  showNormalizeByReference,
}: BenchmarkChartsProps) {
  const [sortByRatio, setSortByRatio] = useState(
    showSortByCompressionRatio ? true : false,
  );
  const [normalize, setNormalize] = useState(false);

  if (!chartData.length) return null;

  const sortedData = sortByRatio
    ? [...chartData].sort((a, b) => a.compression_ratio - b.compression_ratio)
    : chartData;

  return (
    <div>
      {showSortByCompressionRatio && (
        <div style={{ marginBottom: "10px" }}>
          <label style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <input
              type="checkbox"
              checked={sortByRatio}
              onChange={(e) => setSortByRatio(e.target.checked)}
            />
            Sort by compression ratio
          </label>
        </div>
      )}
      {showNormalizeByReference && (
        <div style={{ marginBottom: "10px" }}>
          <label style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <input
              type="checkbox"
              checked={normalize}
              onChange={(e) => setNormalize(e.target.checked)}
            />
            Normalize to best compression
          </label>
        </div>
      )}
      <div
        style={{
          display: "flex",
          flexWrap: "wrap",
          gap: "20px",
        }}
      >
        <BenchmarkBarChart
          title="Compression Ratio"
          data={sortedData}
          dataKey="compression_ratio"
          color="#8884d8"
          xAxisTitle={normalize ? "Fraction of Best Compression" : "Ratio"}
          normalize={normalize}
        />
        <BenchmarkBarChart
          title="Encode Speed (MB/s)"
          data={sortedData}
          dataKey="encode_speed"
          color="#82ca9d"
          xAxisTitle="MB/s"
        />
        <BenchmarkBarChart
          title="Decode Speed (MB/s)"
          data={sortedData}
          dataKey="decode_speed"
          color="#ff7300"
          xAxisTitle="MB/s"
        />
      </div>
    </div>
  );
}
