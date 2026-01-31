import { BenchmarkResult } from "../../../types";
import { formatNumber, formatSize } from "../utils/formatters";
import { columns } from "../table/columns";

export const exportToCsv = (
  data: BenchmarkResult[],
  selectedDataset: string,
) => {
  // Convert data to CSV
  const headers = columns.map((col) => col.header).join(",");
  const rows = data
    .map((row) =>
      columns
        .map((col) => {
          const value = row[col.accessorKey as keyof BenchmarkResult];
          // Format numbers according to their display format
          if (col.accessorKey === "compression_ratio") {
            return `${formatNumber(value as number)}x`;
          } else if (
            col.accessorKey === "encode_time" ||
            col.accessorKey === "decode_time"
          ) {
            return formatNumber(value as number, 4);
          } else if (
            col.accessorKey === "original_size" ||
            col.accessorKey === "compressed_size"
          ) {
            return formatSize(value as number);
          } else if (typeof value === "number") {
            return formatNumber(value);
          }
          return value;
        })
        .join(","),
    )
    .join("\n");
  const csv = `${headers}\n${rows}`;

  // Create and trigger download
  const blob = new Blob([csv], { type: "text/csv" });
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `benchmark-results${selectedDataset ? `-${selectedDataset}` : ""}.csv`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  window.URL.revokeObjectURL(url);
};
