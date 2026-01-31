import React, { useRef } from "react";
import { Range } from "./WorkerTypes";

interface TimeseriesNavigationBarProps {
  width: number;
  height: number;
  totalRange: Range;
  viewRange: Range;
  onViewRangeChange: (range: Range) => void;
}

const TimeseriesNavigationBar: React.FC<TimeseriesNavigationBarProps> = ({
  width,
  height,
  totalRange,
  viewRange,
  onViewRangeChange,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);

  // Constants
  const minMarkerWidth = 25; // Minimum width of the marker in pixels
  const padding = 10; // Padding on left and right
  const barWidth = width - 2 * padding;

  // Convert data range to pixel coordinates
  const rangeToPixel = (value: number): number => {
    const ratio = (value - totalRange.min) / (totalRange.max - totalRange.min);
    return padding + ratio * barWidth;
  };

  // Convert pixel coordinates to data range
  const pixelToRange = (pixel: number): number => {
    const ratio = (pixel - padding) / barWidth;
    return totalRange.min + ratio * (totalRange.max - totalRange.min);
  };

  // Calculate marker position and width
  const markerLeft = rangeToPixel(viewRange.min);
  const rawMarkerWidth = rangeToPixel(viewRange.max) - markerLeft;
  const markerWidth = Math.max(rawMarkerWidth, minMarkerWidth);

  const handleClick = (e: React.MouseEvent) => {
    if (!containerRef.current) return;

    const rect = containerRef.current.getBoundingClientRect();
    const clickX = e.clientX - rect.left;

    // Click on the bar - center the view on click position
    const clickedValue = pixelToRange(clickX);
    const currentSize = viewRange.max - viewRange.min;
    const halfSize = currentSize / 2;

    let newMin = clickedValue - halfSize;
    let newMax = clickedValue + halfSize;

    // Clamp to total range bounds
    if (newMin < totalRange.min) {
      newMin = totalRange.min;
      newMax = newMin + currentSize;
    }
    if (newMax > totalRange.max) {
      newMax = totalRange.max;
      newMin = newMax - currentSize;
    }

    onViewRangeChange({ min: newMin, max: newMax });
  };

  return (
    <div
      ref={containerRef}
      style={{
        width,
        height,
        position: "relative",
        backgroundColor: "#f0f0f0",
        borderRadius: 4,
        cursor: "pointer",
      }}
      onClick={handleClick}
    >
      <div
        style={{
          position: "absolute",
          left: markerLeft,
          width: markerWidth,
          height: "100%",
          backgroundColor: "#007bff",
          borderRadius: 4,
          pointerEvents: "none",
        }}
      />
    </div>
  );
};

export default TimeseriesNavigationBar;
