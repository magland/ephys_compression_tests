import { useEffect, useMemo, useReducer, useState, useCallback } from "react";
import TimeseriesNavigationBar from "./TimeseriesNavigationBar";
import { SupportedTypedArray } from "../../hooks/TimeseriesDataClient";
import { useTimeseriesDataClient } from "../../hooks/useTimeseriesDataClient";
import { Dataset } from "../../types";
import { Margins, Range, WorkerMessage } from "./WorkerTypes";
import { initialState, timeseriesViewReducer } from "./timeseriesViewReducer";

interface TimeseriesViewProps {
  width: number;
  height: number;
  dataset: Dataset;
}

const TimeseriesView: React.FC<TimeseriesViewProps> = ({
  width,
  height,
  dataset,
}) => {
  const { client, error: clientError } = useTimeseriesDataClient(dataset);
  const [dataT, setDataT] = useState<number[] | null>(null);
  const [dataY, setDataY] = useState<SupportedTypedArray | null>(null);
  const [error, setError] = useState<string | null>(clientError);
  const [isLoading, setIsLoading] = useState(false);

  const [canvasElement, setCanvasElement] = useState<HTMLCanvasElement | null>(
    null,
  );
  const [overlayCanvasElement, setOverlayCanvasElement] =
    useState<HTMLCanvasElement | null>(null);
  const [state, dispatch] = useReducer(timeseriesViewReducer, initialState);
  const { selectedIndex, isDragging, lastDragX, xRange } = state;
  const [isWheelEnabled, setIsWheelEnabled] = useState(false);
  const [showHint, setShowHint] = useState(true);

  // Hide hint when user interacts with the graph
  const hideHint = useCallback(() => {
    setShowHint(false);
  }, []);

  // Auto-hide hint after 4 seconds
  useEffect(() => {
    if (showHint) {
      const timer = setTimeout(() => {
        setShowHint(false);
      }, 5000);
      return () => clearTimeout(timer);
    }
  }, [showHint]);

  const [container, setContainer] = useState<HTMLDivElement | null>(null);
  const [worker, setWorker] = useState<Worker | null>(null);
  const [margins] = useState<Margins>({
    left: 50,
    right: 20,
    top: 20,
    bottom: 50,
  });

  // Load data for current range
  useEffect(() => {
    if (!client || !xRange) return;

    const loadRangeData = async () => {
      try {
        setIsLoading(true);
        const start = Math.floor(xRange.min);
        const end = Math.ceil(xRange.max) + 1;
        const rangeData = await client.fetchRange(start, end);
        setDataY(rangeData);
        const dT = Array.from(
          { length: rangeData.length },
          (_, i) => i + start,
        );
        setDataT(dT);
        setError(null);
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Failed to load data range",
        );
      } finally {
        setIsLoading(false);
      }
    };

    loadRangeData();
  }, [client, xRange]);

  // Update xRange when client is initialized
  useEffect(() => {
    if (client) {
      const shape = client.getShape();
      dispatch({
        type: "SET_X_RANGE",
        range: { min: 0, max: Math.min(999, shape - 1) },
      });
    }
  }, [client]);

  // Set up wheel event listener
  useEffect(() => {
    if (!container || !client) return;

    const handleWheel = (e: WheelEvent) => {
      if (!isWheelEnabled) {
        return; // Allow page scrolling if wheel zoom not enabled
      }
      e.preventDefault();

      const rect = container.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const xRatio =
        (x - margins.left) / (width - margins.left - margins.right);

      // Calculate zoom center in data coordinates
      const zoomCenter = xRange.min + (xRange.max - xRange.min) * xRatio;

      // Calculate new range
      const zoomFactor = e.deltaY > 0 ? 1.1 : 1 / 1.1;
      const shape = client.getShape();

      // Ensure we don't zoom out beyond data bounds
      const newMin = Math.max(
        0,
        zoomCenter - (zoomCenter - xRange.min) * zoomFactor,
      );
      const newMax = Math.min(
        shape - 1,
        zoomCenter + (xRange.max - zoomCenter) * zoomFactor,
      );

      dispatch({ type: "SET_X_RANGE", range: { min: newMin, max: newMax } });
    };

    container.addEventListener("wheel", handleWheel, { passive: false });
    return () => {
      container.removeEventListener("wheel", handleWheel);
    };
  }, [container, client, width, margins, xRange, isWheelEnabled]);

  // Set up mouse event listeners for panning
  useEffect(() => {
    if (!container || !client) return;

    const handleMouseDown = (e: MouseEvent) => {
      dispatch({ type: "SET_IS_DRAGGING", isDragging: true });
      dispatch({ type: "SET_LAST_DRAG_X", x: e.clientX });
    };

    const handleMouseMove = (e: MouseEvent) => {
      if (!isDragging || lastDragX === 0) return;

      const deltaX = e.clientX - lastDragX;
      const xRatio = deltaX / (width - margins.left - margins.right);
      const dataDelta = (xRange.max - xRange.min) * xRatio;
      const shape = client.getShape();

      if (xRange.min - dataDelta < 0) return;
      if (xRange.max - dataDelta > shape - 1) return;

      const newMin = xRange.min - dataDelta;
      const newMax = xRange.max - dataDelta;

      // Only update if we're still within bounds
      if (newMin >= 0 && newMax <= shape - 1) {
        dispatch({ type: "SET_X_RANGE", range: { min: newMin, max: newMax } });
      }

      dispatch({ type: "SET_LAST_DRAG_X", x: e.clientX });
    };

    const handleMouseUp = () => {
      dispatch({ type: "SET_IS_DRAGGING", isDragging: false });
      dispatch({ type: "SET_LAST_DRAG_X", x: 0 });
    };

    container.addEventListener("mousedown", handleMouseDown);
    window.addEventListener("mousemove", handleMouseMove);
    window.addEventListener("mouseup", handleMouseUp);

    return () => {
      container.removeEventListener("mousedown", handleMouseDown);
      window.removeEventListener("mousemove", handleMouseMove);
      window.removeEventListener("mouseup", handleMouseUp);
    };
  }, [container, client, width, margins, xRange, isDragging, lastDragX]);

  // Set worker
  useEffect(() => {
    if (!canvasElement) return;
    const worker = new Worker(
      new URL("./TimeseriesViewWorker", import.meta.url),
      {
        type: "module",
      },
    );
    let offscreenCanvas: OffscreenCanvas;
    try {
      offscreenCanvas = canvasElement.transferControlToOffscreen();
    } catch (err) {
      console.warn(err);
      console.warn(
        "Unable to transfer control to offscreen canvas (expected during dev)",
      );
      return;
    }
    const msg: WorkerMessage = {
      type: "initialize",
      canvas: offscreenCanvas,
    };
    worker.postMessage(msg, [offscreenCanvas]);

    setWorker(worker);

    return () => {
      worker.terminate();
    };
  }, [canvasElement]);

  // Calculate yRange from data
  const yRange = useMemo<Range>(() => {
    if (!dataY) return { min: 0, max: 1 };
    return {
      min: computeMin(dataY),
      max: computeMax(dataY),
    };
  }, [dataY]);

  // Handle dimension changes
  useEffect(() => {
    if (!worker) return;
    if (!dataY) return;
    if (!dataT) return;

    const msg: WorkerMessage = {
      type: "render",
      timeseriesT: dataT,
      timeseriesY: Array.from(dataY),
      width,
      height,
      margins,
      xRange,
      yRange,
    };
    worker.postMessage(msg);
  }, [width, height, dataT, dataY, worker, margins, xRange, yRange]);

  // Render cursor on overlay canvas
  useEffect(() => {
    if (!overlayCanvasElement || selectedIndex === null || !dataY) return;
    const ctx = overlayCanvasElement.getContext("2d");
    if (!ctx) return;

    // Clear overlay canvas
    ctx.clearRect(0, 0, width, height);

    // Draw cursor line
    const xRatio = (selectedIndex - xRange.min) / (xRange.max - xRange.min);
    const x = margins.left + xRatio * (width - margins.left - margins.right);
    ctx.beginPath();
    ctx.strokeStyle = "#ff0000";
    ctx.lineWidth = 1;
    ctx.setLineDash([4, 4]);
    ctx.moveTo(x, margins.top);
    ctx.lineTo(x, height - margins.bottom);
    ctx.stroke();
  }, [
    selectedIndex,
    overlayCanvasElement,
    width,
    height,
    margins,
    dataT,
    dataY,
    xRange,
  ]);

  const selectedValue = useMemo(() => {
    if (selectedIndex === -1 || !dataT || !dataY) return null;
    for (let i = 0; i < dataT.length; i++) {
      if (dataT[i] === selectedIndex) {
        return dataY[i];
      }
    }
    return null;
  }, [selectedIndex, dataT, dataY]);

  if (error || clientError) {
    return <div>Error loading data: {error || clientError}</div>;
  }

  if (isLoading && !dataY) {
    return <div>Loading...</div>;
  }

  const handleCanvasClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!overlayCanvasElement || !dataY || isDragging) return;

    // Enable wheel zooming on first click
    if (!isWheelEnabled) {
      setIsWheelEnabled(true);
    }

    const rect = overlayCanvasElement.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const xRatio = (x - margins.left) / (width - margins.left - margins.right);
    const index = Math.round(xRange.min + xRatio * (xRange.max - xRange.min));
    if (index >= 0) {
      dispatch({ type: "SET_SELECTED_INDEX", index });
    }
  };

  return (
    <div style={{ position: "relative", width, height: height + 50 }}>
      <div style={{ marginBottom: 10, height: 20 }}>
        <TimeseriesNavigationBar
          width={width}
          height={20}
          totalRange={{ min: 0, max: client ? client.getShape() - 1 : 999 }}
          viewRange={xRange}
          onViewRangeChange={(range) =>
            dispatch({ type: "SET_X_RANGE", range })
          }
        />
      </div>
      {showHint && (
        <div
          style={{
            position: "absolute",
            top: margins.top + 10,
            right: margins.right + 10,
            display: "flex",
            flexDirection: "column",
            alignItems: "flex-end",
            gap: "8px",
            zIndex: 10,
            opacity: showHint ? 0.8 : 0,
            transition: "opacity 0.5s ease-out",
            pointerEvents: "none",
            fontSize: "12px",
            color: "#666",
          }}
        >
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "4px",
              backgroundColor: "rgba(255, 255, 255, 0.9)",
              padding: "2px 6px",
              borderRadius: "4px",
            }}
          >
            <span>Drag to pan</span>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="#666">
              <path d="M15 3h2v5h-2V3zm4 0h2v5h-2V3zm-4 7h2v5h-2v-5zm4 0h2v5h-2v-5zm-4 7h2v5h-2v-5zm4 0h2v5h-2v-5z" />
            </svg>
          </div>
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "4px",
              backgroundColor: "rgba(255, 255, 255, 0.9)",
              padding: "2px 6px",
              borderRadius: "4px",
            }}
          >
            <span>Scroll to zoom</span>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="#666">
              <path d="M12 3c-4.97 0-9 4.03-9 9s4.03 9 9 9 9-4.03 9-9-4.03-9-9-9zm0 16c-3.86 0-7-3.14-7-7s3.14-7 7-7 7 3.14 7 7-3.14 7-7 7zm1-11h-2v3H8v2h3v3h2v-3h3v-2h-3V8z" />
            </svg>
          </div>
        </div>
      )}
      <div
        ref={setContainer}
        style={{ position: "relative", width, height }}
        onClick={(e) => {
          handleCanvasClick(e);
          hideHint();
        }}
        onMouseDown={hideHint}
      >
        <canvas
          ref={setCanvasElement}
          key={`canvas-${width}-${height}`}
          width={width}
          height={height}
          style={{
            position: "absolute",
            width: "100%",
            height: "100%",
          }}
        />
        <canvas
          ref={setOverlayCanvasElement}
          width={width}
          height={height}
          style={{
            position: "absolute",
            width: "100%",
            height: "100%",
            pointerEvents: "none",
          }}
        />
      </div>
      {selectedIndex !== -1 && dataY && (
        <div style={{ height: 30, padding: "5px 0", color: "#666" }}>
          Index: {selectedIndex}, Value: {selectedValue?.toFixed(3)}
        </div>
      )}
    </div>
  );
};

const computeMin = (data: SupportedTypedArray) => {
  let min = Infinity;
  for (let i = 0; i < data.length; i++) {
    if (data[i] < min) {
      min = data[i];
    }
  }
  return min;
};

const computeMax = (data: SupportedTypedArray) => {
  let max = -Infinity;
  for (let i = 0; i < data.length; i++) {
    if (data[i] > max) {
      max = data[i];
    }
  }
  return max;
};

export default TimeseriesView;
