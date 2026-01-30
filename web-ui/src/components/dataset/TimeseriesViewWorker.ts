// Web worker for rendering timeseries data to canvas

import { Margins, Range, WorkerMessage } from "./WorkerTypes";

// Helper function to find a nice integer tick interval
function getNiceTickInterval(range: number, maxTicks: number): number {
  const minInterval = Math.ceil(range / maxTicks);
  if (minInterval <= 1) return 1;

  const magnitude = Math.pow(10, Math.floor(Math.log10(minInterval)));
  const niceIntervals = [1, 2, 5, 10];

  for (const interval of niceIntervals) {
    const tickInterval = interval * magnitude;
    if (tickInterval >= minInterval) {
      return Math.ceil(tickInterval);
    }
  }
  return Math.ceil(niceIntervals[niceIntervals.length - 1] * magnitude * 10);
}

// Helper function to estimate the width of a number in pixels
// This is an approximation since we can't measure text width directly in a worker
function estimateNumberWidth(num: number): number {
  const numStr = Math.abs(num).toString();
  const digitWidth = 8; // Approximate width of a digit in pixels
  const padding = 4; // Padding between numbers
  return (numStr.length + (num < 0 ? 1 : 0)) * digitWidth + padding;
}

// Helper function to get tick positions
function getTickPositions(
  range: Range,
  width: number,
  considerNumberWidth = false, // Only true for x-axis where we need to handle large integers
): { value: number; x: number }[] {
  let pixelsPerTick = 20; // Default minimum pixels between ticks

  if (considerNumberWidth) {
    // For x-axis, calculate spacing based on largest number width
    const maxAbsValue = Math.max(Math.abs(range.min), Math.abs(range.max));
    const maxNumberWidth = estimateNumberWidth(maxAbsValue);
    pixelsPerTick = Math.max(maxNumberWidth, 20); // Use the larger of estimated width or minimum spacing
  }
  const maxTicks = Math.floor(width / pixelsPerTick);
  const tickInterval = getNiceTickInterval(range.max - range.min, maxTicks);

  const firstTick = Math.ceil(range.min / tickInterval) * tickInterval;
  const lastTick = Math.floor(range.max);

  const ticks: { value: number; x: number }[] = [];
  for (let value = firstTick; value <= lastTick; value += tickInterval) {
    const x = (value - range.min) / (range.max - range.min);
    if (Number.isInteger(value)) {
      ticks.push({ value, x });
    }
  }

  return ticks;
}

let canvas: OffscreenCanvas | null = null;
let ctx: OffscreenCanvasRenderingContext2D | null = null;

function renderTimeseries(
  timeseriesT: number[],
  timeseriesY: number[],
  timeseriesYAll: number[][] | undefined,
  width: number,
  height: number,
  margins: Margins,
  xRange: Range,
  yRange: Range,
) {
  if (!ctx || !canvas) return;

  const context = ctx; // Create a stable reference to satisfy TypeScript

  // Clear canvas
  context.clearRect(0, 0, width, height);

  // Draw axes
  context.strokeStyle = "#666666";
  context.lineWidth = 1;
  context.beginPath();

  // Y axis
  context.moveTo(margins.left, margins.top);
  context.lineTo(margins.left, height - margins.bottom);

  // X axis
  context.moveTo(margins.left, height - margins.bottom);
  context.lineTo(width - margins.right, height - margins.bottom);

  context.stroke();

  // Calculate the drawing area dimensions
  const drawingWidth = width - margins.left - margins.right;
  const drawingHeight = height - margins.top - margins.bottom;

  // Set up clipping region for timeseries
  context.save();
  context.beginPath();
  context.rect(margins.left, margins.top, drawingWidth, drawingHeight);
  context.clip();

  // Calculate scaling factors
  const xScale = drawingWidth / (xRange.max - xRange.min);
  const yScale = drawingHeight / (yRange.max - yRange.min);

  // Draw timeseries - either all channels or single channel
  if (timeseriesYAll && timeseriesYAll.length > 0) {
    // Draw all channels with different colors
    const colors = [
      "#2196f3", // blue
      "#f44336", // red
      "#4caf50", // green
      "#ff9800", // orange
      "#9c27b0", // purple
      "#00bcd4", // cyan
      "#ffeb3b", // yellow
      "#795548", // brown
    ];
    
    timeseriesYAll.forEach((channelY, channelIdx) => {
      context.strokeStyle = colors[channelIdx % colors.length];
      context.lineWidth = 1.5;
      context.beginPath();
      
      let isFirst = true;
      for (let i = 0; i < timeseriesT.length; i++) {
        const x = margins.left + (timeseriesT[i] - xRange.min) * xScale;
        const y = margins.top + drawingHeight - (channelY[i] - yRange.min) * yScale;
        if (isFirst) {
          context.moveTo(x, y);
          isFirst = false;
        } else {
          context.lineTo(x, y);
        }
      }
      context.stroke();
    });
  } else {
    // Draw single channel
    context.strokeStyle = "#2196f3";
    context.lineWidth = 2;
    context.beginPath();

    // Draw the path
    let isFirst = true;
    for (let i = 0; i < timeseriesT.length; i++) {
      const x = margins.left + (timeseriesT[i] - xRange.min) * xScale;
      const y =
        margins.top + drawingHeight - (timeseriesY[i] - yRange.min) * yScale;
      if (isFirst) {
        context.moveTo(x, y);
        isFirst = false;
      } else {
        context.lineTo(x, y);
      }
    }

    context.stroke();
  }

  // Remove clipping before drawing ticks
  context.restore();

  // Draw Y-axis ticks and labels
  const yTicks = getTickPositions(yRange, drawingHeight);

  context.textAlign = "right";
  context.textBaseline = "middle";
  context.fillStyle = "#666666";
  context.font = "12px Arial";

  yTicks.forEach((tick) => {
    const y = margins.top + drawingHeight - tick.x * drawingHeight;

    // Draw tick mark
    context.beginPath();
    context.moveTo(margins.left - 6, y);
    context.lineTo(margins.left, y);
    context.stroke();

    // Draw label
    context.fillText(tick.value.toString(), margins.left - 8, y);
  });

  // Draw X-axis ticks and labels
  const ticks = getTickPositions(xRange, drawingWidth, true); // Consider number width for x-axis

  context.textAlign = "center";
  context.textBaseline = "top";
  context.fillStyle = "#666666";
  context.font = "12px Arial";

  ticks.forEach((tick) => {
    const x = margins.left + tick.x * drawingWidth;

    // Draw tick mark
    context.beginPath();
    context.moveTo(x, height - margins.bottom);
    context.lineTo(x, height - margins.bottom + 6);
    context.stroke();

    // Draw label
    context.fillText(tick.value.toString(), x, height - margins.bottom + 8);
  });
}

self.onmessage = (evt: MessageEvent) => {
  const message = evt.data as WorkerMessage;

  if (message.type === "initialize") {
    canvas = message.canvas;
    ctx = canvas.getContext("2d");
    if (!ctx) {
      self.postMessage({
        type: "error",
        error: "Failed to get canvas context",
      });
      return;
    }
    self.postMessage({ type: "initialized" });
    return;
  }

  if (message.type === "render") {
    throttleRender(() => {
      const {
        timeseriesT,
        timeseriesY,
        timeseriesYAll,
        width,
        height,
        margins,
        xRange,
        yRange,
      } = message;
      renderTimeseries(
        timeseriesT,
        timeseriesY,
        timeseriesYAll,
        width,
        height,
        margins,
        xRange,
        yRange,
      );
      self.postMessage({ type: "render_complete" });
    });
    return;
  }
};

let renderStack: (() => void)[] = [];
let lastRenderTime = 0;

const throttleRender = (callback: () => void) => {
  renderStack.push(callback);
  const checkRender = () => {
    if (renderStack.length === 0) return;
    const elapsed = Date.now() - lastRenderTime;
    if (elapsed > 100) {
      lastRenderTime = Date.now();
      renderStack[renderStack.length - 1]();
      renderStack = [];
    } else {
      setTimeout(checkRender, 150);
    }
  };
  checkRender();
};

export {}; // Needed for TypeScript modules
