import { Algorithm, BenchmarkData } from "../../types";
import { BaseContent } from "../shared/BaseContent";
import "../shared/ContentStyles.css";

interface AlgorithmContentProps {
  algorithm: Algorithm;
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

export const AlgorithmContent = ({
  algorithm,
  benchmarkData,
  chartData,
}: AlgorithmContentProps) => {
  return (
    <BaseContent
      item={algorithm}
      benchmarkData={benchmarkData}
      chartData={chartData}
      tagNavigationPrefix="/algorithms"
      filterKey="algorithm"
      showSortByCompressionRatio={false}
      showNormalizeByReference={true}
    />
  );
};
