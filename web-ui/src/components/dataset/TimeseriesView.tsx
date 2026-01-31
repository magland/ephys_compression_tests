import { useEffect, useMemo, useReducer, useState, useCallback } from "react";
import TimeseriesNavigationBar from "./TimeseriesNavigationBar";
import { SupportedTypedArray } from "../../hooks/TimeseriesDataClient";
import { useTimeseriesDataClient } from "../../hooks/useTimeseriesDataClient";
import { Dataset } from "../../types";
import { Margins, Range, WorkerMessage } from "./WorkerTypes";
import { initialState, timeseriesViewReducer } from "./timeseriesViewReducer";
import { ReconstructedDataInfo, ComparisonMode } from "../../types/comparison";
import { TimeseriesDataClient } from "../../hooks/TimeseriesDataClient";

interface TimeseriesViewProps {
  width: number;
  height: number;
  dataset: Dataset;
  comparisonMode?: ComparisonMode;
  reconstructedInfo?: ReconstructedDataInfo | null;
}

const TimeseriesView: React.FC<TimeseriesViewProps> = ({
  width,
  height,
  dataset,
  comparisonMode = "original",
  reconstructedInfo = null,
}) => {
  const { client, error: clientError } = useTimeseriesDataClient(dataset);
  const [dataT, setDataT] = useState<number[] | null>(null);
  const [dataY, setDataY] = useState<SupportedTypedArray | null>(null);
  const [dataYAll, setDataYAll] = useState<SupportedTypedArray[] | null>(null);
  const [dataYReconstructed, setDataYReconstructed] = useState<SupportedTypedArray | null>(null);
  const [dataYResiduals, setDataYResiduals] = useState<SupportedTypedArray | null>(null);
  const [reconstructedClient, setReconstructedClient] = useState<TimeseriesDataClient | null>(null);
  const [error, setError] = useState<string | null>(clientError);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedChannel, setSelectedChannel] = useState<number | "all">(0);
  const [numChannels, setNumChannels] = useState<number>(1);

  const [canvasElement, setCanvasElement] = useState<HTMLCanvasElement | null>(
    null,
  );
  const [overlayCanvasElement, setOverlayCanvasElement] =
    useState<HTMLCanvasElement | null>(null);
  const [state, dispatch] = useReducer(timeseriesViewReducer, initialState);
  const { selectedIndex, isDragging, lastDragX, xRange } = state;
  // Wheel zooming is disabled because it causes the page to scroll when the user
  // tries to scroll the timeseries view, creating a poor user experience.
  // Instead, we provide explicit zoom control buttons.
  const [isWheelEnabled] = useState(false); // Keep state for potential future use, but always false
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
        
        if (selectedChannel === "all") {
          // Load all channels
          const allChannelData = await Promise.all(
            Array.from({ length: numChannels }, (_, ch) =>
              client.fetchRange(start, end, ch)
            )
          );
          setDataYAll(allChannelData);
          setDataY(null);
        } else {
          // Load single channel
          const rangeData = await client.fetchRange(start, end, selectedChannel);
          setDataY(rangeData);
          setDataYAll(null);
        }
        
        const dT = Array.from(
          { length: end - start },
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
  }, [client, xRange, selectedChannel, numChannels]);

  // Initialize reconstructed data client when reconstructedInfo changes
  useEffect(() => {
    if (!reconstructedInfo) {
      setReconstructedClient(null);
      setDataYReconstructed(null);
      setDataYResiduals(null);
      return;
    }

    // When a reconstruction is selected for comparison, switch from "all" to channel 0
    if (selectedChannel === "all") {
      setSelectedChannel(0);
    }

    const initClient = async () => {
      try {
        const client = await TimeseriesDataClient.create(
          reconstructedInfo.datasetJsonUrl,
          reconstructedInfo.reconstructedUrl,
          1000
        );
        setReconstructedClient(client);
      } catch (err) {
        console.error("Failed to initialize reconstructed data client:", err);
        setError("Failed to load reconstructed data");
      }
    };

    initClient();
  }, [reconstructedInfo, selectedChannel]);

  // Load reconstructed data for current range
  useEffect(() => {
    if (!reconstructedClient || !xRange || selectedChannel === "all" || comparisonMode === "original") {
      setDataYReconstructed(null);
      setDataYResiduals(null);
      return;
    }

    const loadReconstructedData = async () => {
      try {
        const start = Math.floor(xRange.min);
        const end = Math.ceil(xRange.max) + 1;
        const channel = typeof selectedChannel === "number" ? selectedChannel : 0;
        
        const reconstructedData = await reconstructedClient.fetchRange(start, end, channel);
        setDataYReconstructed(reconstructedData);

        // Compute residuals if we have both original and reconstructed
        if (dataY && reconstructedData.length === dataY.length) {
          const residuals = new Float32Array(dataY.length);
          for (let i = 0; i < dataY.length; i++) {
            residuals[i] = dataY[i] - reconstructedData[i];
          }
          setDataYResiduals(residuals);
        }
      } catch (err) {
        console.error("Failed to load reconstructed data:", err);
      }
    };

    loadReconstructedData();
  }, [reconstructedClient, xRange, selectedChannel, dataY, comparisonMode]);

  // Update xRange when client is initialized
  useEffect(() => {
    if (client) {
      const shape = client.getShape();
      const channels = client.getNumChannels();
      setNumChannels(channels);
      // Default to "all" if 20 or fewer channels, otherwise default to channel 0
      setSelectedChannel(channels > 1 && channels <= 20 ? "all" : 0);
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
      e.stopPropagation();

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
  }, [container, client, width, margins, isWheelEnabled]);

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
    if (dataYAll) {
      // Calculate range across all channels
      let min = Infinity;
      let max = -Infinity;
      for (const channelData of dataYAll) {
        const channelMin = computeMin(channelData);
        const channelMax = computeMax(channelData);
        if (channelMin < min) min = channelMin;
        if (channelMax > max) max = channelMax;
      }
      return { min, max };
    } else if (dataY) {
      let min = computeMin(dataY);
      let max = computeMax(dataY);

      // When comparing with reconstructed data, include that data in the range calculation
      if (comparisonMode === "overlay" || comparisonMode === "side-by-side") {
        if (dataYReconstructed) {
          const reconstructedMin = computeMin(dataYReconstructed);
          const reconstructedMax = computeMax(dataYReconstructed);
          if (reconstructedMin < min) min = reconstructedMin;
          if (reconstructedMax > max) max = reconstructedMax;
        }
      } else if (comparisonMode === "residuals") {
        // For residuals mode, use only the residuals range
        if (dataYResiduals) {
          min = computeMin(dataYResiduals);
          max = computeMax(dataYResiduals);
        }
      }

      return { min, max };
    }
    return { min: 0, max: 1 };
  }, [dataY, dataYAll, dataYReconstructed, dataYResiduals, comparisonMode]);

  // Handle dimension changes
  useEffect(() => {
    if (!worker) return;
    if (!dataT) return;
    if (!dataY && !dataYAll) return;

    const msg: WorkerMessage = {
      type: "render",
      timeseriesT: dataT,
      timeseriesY: dataY ? Array.from(dataY) : [],
      timeseriesYAll: dataYAll ? dataYAll.map(ch => Array.from(ch)) : undefined,
      timeseriesYReconstructed: dataYReconstructed ? Array.from(dataYReconstructed) : undefined,
      timeseriesYResiduals: dataYResiduals ? Array.from(dataYResiduals) : undefined,
      comparisonMode: comparisonMode,
      width,
      height,
      margins,
      xRange,
      yRange,
    };
    worker.postMessage(msg);
  }, [width, height, dataT, dataY, dataYAll, dataYReconstructed, dataYResiduals, comparisonMode, worker, margins, xRange, yRange]);

  // Render cursor on overlay canvas
  useEffect(() => {
    if (!overlayCanvasElement || selectedIndex === null || (!dataY && !dataYAll)) return;
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
    dataYAll,
    xRange,
  ]);

  const selectedValue = useMemo(() => {
    if (selectedIndex === -1 || !dataT) return null;
    
    if (dataYAll) {
      // Return all channel values
      const values: number[] = [];
      for (let ch = 0; ch < dataYAll.length; ch++) {
        for (let i = 0; i < dataT.length; i++) {
          if (dataT[i] === selectedIndex) {
            values.push(dataYAll[ch][i]);
            break;
          }
        }
      }
      return values.length > 0 ? values : null;
    } else if (dataY) {
      // Return single channel value
      for (let i = 0; i < dataT.length; i++) {
        if (dataT[i] === selectedIndex) {
          return dataY[i];
        }
      }
    }
    return null;
  }, [selectedIndex, dataT, dataY, dataYAll]);

  if (error || clientError) {
    return <div>Error loading data: {error || clientError}</div>;
  }

  if (isLoading && !dataY) {
    return <div>Loading...</div>;
  }

  const handleCanvasClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!overlayCanvasElement || (!dataY && !dataYAll) || isDragging) return;

    const rect = overlayCanvasElement.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const xRatio = (x - margins.left) / (width - margins.left - margins.right);
    const index = Math.round(xRange.min + xRatio * (xRange.max - xRange.min));
    if (index >= 0) {
      dispatch({ type: "SET_SELECTED_INDEX", index });
    }
  };

  // Zoom control functions - zoom centered on the selected index (current timepoint)
  const handleZoomIn = () => {
    if (!client) return;
    // Use selectedIndex as center if set, otherwise use view center
    const center = selectedIndex !== -1 ? selectedIndex : (xRange.min + xRange.max) / 2;
    const currentRange = xRange.max - xRange.min;
    const newRange = currentRange / 1.5; // Zoom in by 1.5x
    const newMin = Math.max(0, center - newRange / 2);
    const newMax = Math.min(client.getShape() - 1, center + newRange / 2);
    dispatch({ type: "SET_X_RANGE", range: { min: newMin, max: newMax } });
  };

  const handleZoomOut = () => {
    if (!client) return;
    // Use selectedIndex as center if set, otherwise use view center
    const center = selectedIndex !== -1 ? selectedIndex : (xRange.min + xRange.max) / 2;
    const currentRange = xRange.max - xRange.min;
    const newRange = currentRange * 1.5; // Zoom out by 1.5x
    const shape = client.getShape();
    const newMin = Math.max(0, center - newRange / 2);
    const newMax = Math.min(shape - 1, center + newRange / 2);
    dispatch({ type: "SET_X_RANGE", range: { min: newMin, max: newMax } });
  };

  const handleZoomReset = () => {
    if (!client) return;
    const shape = client.getShape();
    dispatch({
      type: "SET_X_RANGE",
      range: { min: 0, max: Math.min(999, shape - 1) },
    });
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
      {numChannels > 1 && (
        <div style={{ marginBottom: 10, display: "flex", alignItems: "center", gap: 8 }}>
          <label htmlFor="channel-select" style={{ fontSize: "14px", color: "#666" }}>
            Channel:
          </label>
          <select
            id="channel-select"
            value={selectedChannel}
            onChange={(e) => {
              const value = e.target.value;
              setSelectedChannel(value === "all" ? "all" : Number(value));
            }}
            style={{
              padding: "4px 8px",
              fontSize: "14px",
              borderRadius: "4px",
              border: "1px solid #ccc",
              backgroundColor: "white",
              cursor: "pointer",
            }}
          >
            <option value="all">All (overlay)</option>
            {Array.from({ length: numChannels }, (_, i) => (
              <option key={i} value={i}>
                {i}
              </option>
            ))}
          </select>
        </div>
      )}
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
        </div>
      )}
      {/* Zoom control buttons - positioned at bottom right to avoid blocking channel selector */}
      <div
        style={{
          position: "absolute",
          bottom: margins.bottom + 10,
          right: margins.right + 10,
          display: "flex",
          gap: "6px",
          zIndex: 10,
        }}
      >
        <button
          onClick={handleZoomIn}
          disabled={!client}
          style={{
            padding: "6px 8px",
            fontSize: "14px",
            borderRadius: "4px",
            border: "1px solid #ccc",
            backgroundColor: "white",
            cursor: client ? "pointer" : "not-allowed",
            opacity: client ? 1 : 0.5,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
          }}
          title="Zoom in"
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="11" cy="11" r="8" />
            <path d="M21 21l-4.35-4.35" />
            <line x1="8" y1="11" x2="14" y2="11" />
            <line x1="11" y1="8" x2="11" y2="14" />
          </svg>
        </button>
        <button
          onClick={handleZoomOut}
          disabled={!client}
          style={{
            padding: "6px 8px",
            fontSize: "14px",
            borderRadius: "4px",
            border: "1px solid #ccc",
            backgroundColor: "white",
            cursor: client ? "pointer" : "not-allowed",
            opacity: client ? 1 : 0.5,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
          }}
          title="Zoom out"
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="11" cy="11" r="8" />
            <path d="M21 21l-4.35-4.35" />
            <line x1="8" y1="11" x2="14" y2="11" />
          </svg>
        </button>
        <button
          onClick={handleZoomReset}
          disabled={!client}
          style={{
            padding: "6px 8px",
            fontSize: "14px",
            borderRadius: "4px",
            border: "1px solid #ccc",
            backgroundColor: "white",
            cursor: client ? "pointer" : "not-allowed",
            opacity: client ? 1 : 0.5,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
          }}
          title="Reset zoom"
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8" />
            <path d="M21 3v5h-5" />
            <path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16" />
            <path d="M3 21v-5h5" />
          </svg>
        </button>
      </div>
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
      {selectedIndex !== -1 && selectedValue && (
        <div style={{ height: 30, padding: "5px 0", color: "#666" }}>
          Index: {selectedIndex},{" "}
          {Array.isArray(selectedValue)
            ? `Values: [${selectedValue.slice(0, 5).map(v => v.toFixed(3)).join(", ")}${selectedValue.length > 5 ? ", ..." : ""}]`
            : `Value: ${selectedValue.toFixed(3)}`}
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
