import { Dataset, BenchmarkData } from "../../types";
import { useEffect, useRef, useState } from "react";
import TimeseriesView from "./TimeseriesView";
import { BaseContent } from "../shared/BaseContent";
import { LossyAlgorithmSelector } from "./LossyAlgorithmSelector";
import { ComparisonModeSelector } from "./ComparisonModeSelector";
import { ReconstructedDataInfo, ComparisonMode } from "../../types/comparison";
import "../shared/ContentStyles.css";

interface DatasetContentProps {
  dataset: Dataset;
  benchmarkData: BenchmarkData | null;
  chartData: Array<{
    algorithmOrDataset: string;
    compression_ratio: number;
    reference_compression_ratio: number | null;
    encode_speed: number;
    decode_speed: number;
    rmse?: number;
    tags: string[];
  }>;
}

export const DatasetContent = ({
  dataset,
  benchmarkData,
  chartData,
}: DatasetContentProps) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [containerWidth, setContainerWidth] = useState(1200);
  const [reconstructedInfo, setReconstructedInfo] = useState<ReconstructedDataInfo | null>(null);
  const [comparisonMode, setComparisonMode] = useState<ComparisonMode>("original");

  useEffect(() => {
    if (!containerRef.current) return;

    const resizeObserver = new ResizeObserver((entries) => {
      for (const entry of entries) {
        setContainerWidth(entry.contentRect.width - 32);
      }
    });

    resizeObserver.observe(containerRef.current);

    return () => {
      resizeObserver.disconnect();
    };
  }, []);

  const downloadSection =
    dataset.data_url_npy || dataset.data_url_raw ? (
      <div>
        <span className="metadata-label">Download: </span>
        <span style={{ display: "inline-flex", gap: "0.5rem" }}>
          {dataset.data_url_npy && (
            <a
              href={dataset.data_url_npy}
              download={`${dataset.name}-${dataset.version}.npy`}
              className="download-link"
            >
              NPY
            </a>
          )}
          {dataset.data_url_raw && (
            <a
              href={dataset.data_url_raw}
              download={`${dataset.name}-${dataset.version}.dat`}
              className="download-link"
            >
              RAW
            </a>
          )}
        </span>
      </div>
    ) : null;

  const timeseriesSection = (
    <div className="content-container">
      {benchmarkData && (
        <>
          <LossyAlgorithmSelector
            dataset={dataset}
            benchmarkResults={benchmarkData.results}
            selectedAlgorithm={reconstructedInfo?.algorithm || null}
            onSelectAlgorithm={(info) => {
              setReconstructedInfo(info);
              if (info === null) {
                setComparisonMode("original");
              }
            }}
          />
          {reconstructedInfo && (
            <ComparisonModeSelector
              mode={comparisonMode}
              onModeChange={setComparisonMode}
            />
          )}
        </>
      )}
      <div
        ref={containerRef}
        style={{
          width: "100%",
          height: "300px",
          backgroundColor: "#f5f5f5",
          borderRadius: "4px",
          padding: "1rem",
        }}
      >
        <TimeseriesView
          width={containerWidth}
          height={250}
          dataset={dataset}
          comparisonMode={comparisonMode}
          reconstructedInfo={reconstructedInfo}
        />
      </div>
    </div>
  );

  return (
    <BaseContent
      item={dataset}
      benchmarkData={benchmarkData}
      chartData={chartData}
      tagNavigationPrefix="/datasets"
      filterKey="dataset"
      downloadSection={downloadSection}
      additionalContent={timeseriesSection}
      showSortByCompressionRatio={true}
    />
  );
};
