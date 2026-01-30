import { useNavigate } from "react-router-dom";
import { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import { BenchmarkData } from "../../types";
import { BenchmarkCharts } from "../benchmark/charts/BenchmarkCharts";
import { BenchmarkScatterPlots } from "../benchmark/charts/BenchmarkScatterPlots";
import { BenchmarkTable } from "../benchmark/table/BenchmarkTable";
import "./ContentStyles.css";

export interface BaseItem {
  name: string;
  description: string;
  long_description?: string;
  version: string;
  tags: string[];
  source_file?: string;
}

interface BaseContentProps {
  item: BaseItem;
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
  tagNavigationPrefix: string;
  filterKey: "dataset" | "algorithm";
  downloadSection?: React.ReactNode;
  additionalContent?: React.ReactNode;
  showSortByCompressionRatio?: boolean;
  showNormalizeByReference?: boolean;
}

export const BaseContent = ({
  item,
  benchmarkData,
  chartData,
  tagNavigationPrefix,
  filterKey,
  downloadSection,
  additionalContent,
  showSortByCompressionRatio,
  showNormalizeByReference,
}: BaseContentProps) => {
  const navigate = useNavigate();
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <div>
      <div className="content-container">
        <p className="content-header">
          <strong>{item.name}</strong> | {item.description}
        </p>
        {item.long_description && (
          <>
            <button
              className="description-toggle"
              onClick={() => setIsExpanded(!isExpanded)}
            >
              {isExpanded ? "View less" : "Read more"}
            </button>
            {isExpanded && (
              <div className="long-description">
                <ReactMarkdown
                  remarkPlugins={[remarkMath]}
                  rehypePlugins={[rehypeKatex]}
                >
                  {item.long_description}
                </ReactMarkdown>
              </div>
            )}
          </>
        )}
      </div>
      <div className="metadata-section">
        <div>
          <span className="metadata-label">Version: </span>
          <span className="metadata-value">{item.version}</span>
        </div>
        <div>
          <span className="metadata-label">Tags: </span>
          {item.tags.map((tag) => (
            <span
              key={tag}
              className="tag"
              onClick={() => navigate(`${tagNavigationPrefix}?tag=${tag}`)}
            >
              {tag}
            </span>
          ))}
        </div>
        {downloadSection}
        {item.source_file && (
          <div>
            <span className="metadata-label">Source: </span>
            <a
              href={item.source_file}
              target="_blank"
              rel="noopener noreferrer"
              className="source-link"
            >
              View
            </a>
          </div>
        )}
      </div>
      {additionalContent}
      {benchmarkData && (
        <>
          <div className="benchmark-section">
            <h2 className="benchmark-title">Benchmark Results</h2>
            <BenchmarkCharts
              chartData={chartData}
              showSortByCompressionRatio={showSortByCompressionRatio}
              showNormalizeByReference={showNormalizeByReference}
            />
            {filterKey === "dataset" && (
              <BenchmarkScatterPlots chartData={chartData} />
            )}
          </div>
          <div className="benchmark-section">
            <BenchmarkTable
              results={benchmarkData.results.filter(
                (result) => result[filterKey] === item.name,
              )}
            />
          </div>
        </>
      )}
    </div>
  );
};
