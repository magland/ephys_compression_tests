import { createColumnHelper } from "@tanstack/react-table";
import { BenchmarkResult } from "../../../types";
import { formatNumber, formatSize } from "../utils/formatters";
import { Link } from "react-router-dom";

const columnHelper = createColumnHelper<BenchmarkResult>();

export const columns = [
  columnHelper.accessor("dataset", {
    header: "Dataset",
    cell: (info) => (
      <Link
        to={`/dataset/${info.getValue()}`}
        style={{ color: "#2563eb", textDecoration: "none" }}
        onMouseEnter={(e) =>
          (e.currentTarget.style.textDecoration = "underline")
        }
        onMouseLeave={(e) => (e.currentTarget.style.textDecoration = "none")}
      >
        {info.getValue()}
      </Link>
    ),
  }),
  columnHelper.accessor("algorithm", {
    header: "Algorithm",
    cell: (info) => (
      <Link
        to={`/algorithm/${info.getValue()}`}
        style={{ color: "#2563eb", textDecoration: "none" }}
        onMouseEnter={(e) =>
          (e.currentTarget.style.textDecoration = "underline")
        }
        onMouseLeave={(e) => (e.currentTarget.style.textDecoration = "none")}
      >
        {info.getValue()}
      </Link>
    ),
  }),
  columnHelper.accessor("compression_ratio", {
    header: "Compression Ratio",
    cell: (info) => `${formatNumber(info.getValue())}`,
    sortingFn: (rowA, rowB) => {
      const a = rowA.original.compression_ratio;
      const b = rowB.original.compression_ratio;
      return a - b;
    },
  }),
  columnHelper.accessor("encode_time", {
    header: "Encode Time (s)",
    cell: (info) => formatNumber(info.getValue(), 4),
    sortingFn: (rowA, rowB) => {
      const a = rowA.original.encode_time;
      const b = rowB.original.encode_time;
      return a - b;
    },
  }),
  columnHelper.accessor("decode_time", {
    header: "Decode Time (s)",
    cell: (info) => formatNumber(info.getValue(), 4),
    sortingFn: (rowA, rowB) => {
      const a = rowA.original.decode_time;
      const b = rowB.original.decode_time;
      return a - b;
    },
  }),
  columnHelper.accessor("encode_mb_per_sec", {
    header: "Encode Speed (MB/s)",
    cell: (info) => formatNumber(info.getValue()),
    sortingFn: (rowA, rowB) => {
      const a = rowA.original.encode_mb_per_sec;
      const b = rowB.original.encode_mb_per_sec;
      return a - b;
    },
  }),
  columnHelper.accessor("decode_mb_per_sec", {
    header: "Decode Speed (MB/s)",
    cell: (info) => formatNumber(info.getValue()),
    sortingFn: (rowA, rowB) => {
      const a = rowA.original.decode_mb_per_sec;
      const b = rowB.original.decode_mb_per_sec;
      return a - b;
    },
  }),
  columnHelper.accessor("original_size", {
    header: "Original Size",
    cell: (info) => formatSize(info.getValue()),
    sortingFn: (rowA, rowB) => {
      const a = rowA.original.original_size;
      const b = rowB.original.original_size;
      return a - b;
    },
  }),
  columnHelper.accessor("compressed_size", {
    header: "Compressed Size",
    cell: (info) => formatSize(info.getValue()),
    sortingFn: (rowA, rowB) => {
      const a = rowA.original.compressed_size;
      const b = rowB.original.compressed_size;
      return a - b;
    },
  }),
];
