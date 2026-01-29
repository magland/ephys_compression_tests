import { useMemo } from "react";
import { BenchmarkResult } from "../types";

export function useBenchmarkChartData(
  results: BenchmarkResult[],
  selectedDataset?: string | null,
  selectedAlgorithm?: string | null,
) {
  return useMemo(() => {
    if (selectedDataset) {
      return results
        .filter((row) => row.dataset === selectedDataset)
        .map((row) => ({
          algorithmOrDataset: row.algorithm,
          compression_ratio: row.compression_ratio,
          reference_compression_ratio: null,
          encode_speed: row.encode_mb_per_sec,
          decode_speed: row.decode_mb_per_sec,
        }));
    } else if (selectedAlgorithm) {
      return results
        .filter((row) => row.algorithm === selectedAlgorithm)
        .map((row) => ({
          algorithmOrDataset: row.dataset,
          compression_ratio: row.compression_ratio,
          reference_compression_ratio: Math.max(
            ...results
              .filter((r) => r.dataset === row.dataset)
              .map((r) => r.compression_ratio),
          ),
          encode_speed: row.encode_mb_per_sec,
          decode_speed: row.decode_mb_per_sec,
        }));
    }
    return [];
  }, [results, selectedDataset, selectedAlgorithm]);
}
