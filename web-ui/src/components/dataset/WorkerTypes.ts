import { ComparisonMode } from "../../types/comparison";

export interface Range {
  min: number;
  max: number;
}

export interface Margins {
  left: number;
  right: number;
  top: number;
  bottom: number;
}

export type WorkerMessage =
  | { type: "initialize"; canvas: OffscreenCanvas }
  | {
      type: "render";
      timeseriesT: number[];
      timeseriesY: number[];
      timeseriesYAll?: number[][]; // For multi-channel overlay
      timeseriesYReconstructed?: number[]; // For comparison with lossy reconstruction
      timeseriesYResiduals?: number[]; // For showing residuals
      comparisonMode?: ComparisonMode;
      width: number;
      height: number;
      margins: Margins;
      xRange: Range;
      yRange: Range;
    };
