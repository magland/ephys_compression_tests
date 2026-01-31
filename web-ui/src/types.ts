export interface BenchmarkResult {
  dataset: string;
  algorithm: string;
  algorithm_version: string;
  dataset_version: string;
  system_version: string;
  compression_ratio: number;
  encode_time: number;
  decode_time: number;
  encode_mb_per_sec: number;
  decode_mb_per_sec: number;
  original_size: number;
  compressed_size: number;
  array_shape: number[];
  array_dtype: string;
  timestamp: number;
  rmse?: number;
  max_error?: number;
  reconstructed_url_raw?: string;
}

export interface Algorithm {
  name: string;
  description: string;
  long_description?: string;
  version: string;
  tags: string[];
  source_file?: string;
}

export interface Dataset {
  name: string;
  description: string;
  long_description?: string;
  version: string;
  tags: string[];
  source_file?: string;
  data_url_npy?: string; // URL to download the dataset as .npy
  data_url_raw?: string; // URL to download the raw dataset as .dat
  data_url_json?: string; // URL to download the dataset info as .json (dtype and shape)
}

export interface BenchmarkData {
  results: BenchmarkResult[];
  algorithms: Algorithm[];
  datasets: Dataset[];
}

export interface TabItem {
  id: string;
  label: string;
  route: string;
}

export interface TabsState {
  tabs: TabItem[];
  activeTabId: string;
}

export type TabAction =
  | { type: "ADD_TAB"; payload: { id: string; label: string; route: string } }
  | { type: "SET_ACTIVE_TAB"; payload: string }
  | { type: "REORDER_TABS"; payload: { fromIndex: number; toIndex: number } };
