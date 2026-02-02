import { useMemo } from "react";
import { Algorithm, BenchmarkResult } from "../types";

export function useBenchmarkChartData(
  results: BenchmarkResult[],
  algorithms: Algorithm[],
  selectedDataset?: string | null,
  selectedAlgorithm?: string | null,
) {
  return useMemo(() => {
    if (selectedDataset) {
      return results
        .filter((row) => row.dataset === selectedDataset)
        .map((row) => {
          const algorithm = algorithms.find((a) => a.name === row.algorithm);
          return {
            algorithmOrDataset: row.algorithm,
            compression_ratio: row.compression_ratio,
            reference_compression_ratio: null,
            encode_speed: row.encode_mb_per_sec,
            decode_speed: row.decode_mb_per_sec,
            rmse: row.rmse,
            max_error: row.max_error,
            tags: algorithm?.tags || [],
          };
        });
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
          rmse: row.rmse,
          max_error: row.max_error,
          tags: [],
        }));
    }
    return [];
  }, [results, algorithms, selectedDataset, selectedAlgorithm]);
}
