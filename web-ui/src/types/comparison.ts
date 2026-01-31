export type ComparisonMode = "original" | "overlay" | "residuals" | "side-by-side";

export interface ReconstructedDataInfo {
  algorithm: string;
  rmse: number;
  max_error: number;
  reconstructedUrl: string;
  datasetUrl: string;
  datasetJsonUrl: string;
}
