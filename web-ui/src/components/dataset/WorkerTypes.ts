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
      width: number;
      height: number;
      margins: Margins;
      xRange: Range;
      yRange: Range;
    };
