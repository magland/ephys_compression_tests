import Plot from "react-plotly.js";
import { useState } from "react";

interface ChartData {
  algorithmOrDataset: string;
  compression_ratio: number;
  encode_speed: number;
  decode_speed: number;
  tags: string[];
}

interface BenchmarkScatterPlotsProps {
  chartData: ChartData[];
}

export function BenchmarkScatterPlots({
  chartData,
}: BenchmarkScatterPlotsProps) {
  const [showLabels, setShowLabels] = useState(false);
  const [showLossyAlgs, setShowLossyAlgs] = useState(true);

  if (!chartData.length) return null;

  // Filter data based on showLossyAlgs
  const filteredData = showLossyAlgs
    ? chartData
    : chartData.filter((d) => !d.tags.includes("lossy"));

  const uniqueAlgorithms = Array.from(
    new Set(filteredData.map((d) => d.algorithmOrDataset)),
  );

  const colors = [
    "#1f77b4", // blue
    "#ff7f0e", // orange
    "#2ca02c", // green
    "#d62728", // red
    "#9467bd", // purple
    "#8c564b", // brown
    "#e377c2", // pink
    "#7f7f7f", // gray
  ];

  const markers = ["circle", "square", "diamond", "triangle-up", "star"];

  // Create traces for each algorithm
  const traces = uniqueAlgorithms.flatMap((algo, i) => {
    const algoData = filteredData.filter((d) => d.algorithmOrDataset === algo);
    const isLossy = algoData.length > 0 && algoData[0].tags.includes("lossy");
    const displayName = isLossy ? `${algo}*` : algo;
    const baseTrace = {
      name: displayName,
      mode: showLabels ? ("markers+text" as const) : ("markers" as const),
      marker: {
        color: isLossy ? "red" : colors[i % colors.length],
        symbol: markers[Math.floor(i / colors.length) % markers.length],
        size: 10,
      },
      text: showLabels ? algoData.map(() => displayName) : [],
      textposition: "top center" as const,
      textfont: isLossy ? { color: "red" } : undefined,
      showlegend: true,
      legendgroup: algo,
    };

    return [
      // Compression Ratio vs Decode Speed (upper left)
      {
        ...baseTrace,
        x: algoData.map((d) => d.compression_ratio),
        y: algoData.map((d) => d.decode_speed),
        xaxis: "x" as const,
        yaxis: "y" as const,
        showlegend: true,
      },
      // Compression Ratio vs Encode Speed (lower left)
      {
        ...baseTrace,
        x: algoData.map((d) => d.compression_ratio),
        y: algoData.map((d) => d.encode_speed),
        xaxis: "x2" as const,
        yaxis: "y2" as const,
        showlegend: false,
      },
      // Decode Speed vs Encode Speed (lower right)
      {
        ...baseTrace,
        x: algoData.map((d) => d.decode_speed),
        y: algoData.map((d) => d.encode_speed),
        xaxis: "x3" as const,
        yaxis: "y3" as const,
        showlegend: false,
      },
    ];
  });

  return (
    <div style={{ margin: "20px 0" }}>
      <div style={{ marginBottom: "10px" }}>
        <h2 style={{ marginBottom: "10px" }}>Performance Relationships</h2>
        <div style={{ display: "flex", gap: "16px" }}>
          <label style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <input
              type="checkbox"
              checked={showLabels}
              onChange={(e) => setShowLabels(e.target.checked)}
            />
            Show point labels
          </label>
          <label style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <input
              type="checkbox"
              checked={showLossyAlgs}
              onChange={(e) => setShowLossyAlgs(e.target.checked)}
            />
            Show lossy algs
          </label>
        </div>
      </div>
      <Plot
        data={traces}
        layout={{
          width: 1000,
          height: 670,
          grid: {
            rows: 2,
            columns: 2,
            pattern: "independent",
          },
          xaxis: {
            title: "Compression Ratio",
            domain: [0, 0.45],
          },
          yaxis: {
            title: "Decode Speed (MB/s)",
            domain: [0.55, 1],
          },
          xaxis2: {
            title: "Compression Ratio",
            domain: [0, 0.45],
          },
          yaxis2: {
            title: "Encode Speed (MB/s)",
            domain: [0, 0.45],
          },
          xaxis3: {
            title: "Decode Speed (MB/s)",
            domain: [0.55, 1],
          },
          yaxis3: {
            title: "Encode Speed (MB/s)",
            domain: [0, 0.45],
          },
          showlegend: true,
          legend: {
            x: 1.08,
            y: 1,
            xanchor: "left" as const,
            yanchor: "top" as const,
          },
          margin: {
            l: 60,
            r: 40,
            t: 20,
            b: 60,
          },
        }}
        config={{
          displayModeBar: true,
          displaylogo: false,
          modeBarButtonsToRemove: [
            "lasso2d",
            "select2d",
            "hoverClosestCartesian",
            "hoverCompareCartesian",
          ],
        }}
      />
    </div>
  );
}
