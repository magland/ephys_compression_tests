import { useEffect, useState } from "react";
import { Dataset } from "../types";

const getDtypeSize = (dtype: string): number => {
  switch (dtype) {
    case "uint8":
      return 1;
    case "uint16":
      return 2;
    case "uint32":
      return 4;
    case "int16":
      return 2;
    case "int32":
      return 4;
    default:
      throw new Error(`Unsupported dtype: ${dtype}`);
  }
};

const createTypedArray = (buffer: ArrayBuffer, dtype: string): number[] => {
  switch (dtype) {
    case "uint8":
      return Array.from(new Uint8Array(buffer));
    case "uint16":
      return Array.from(new Uint16Array(buffer));
    case "uint32":
      return Array.from(new Uint32Array(buffer));
    case "int16":
      return Array.from(new Int16Array(buffer));
    case "int32":
      return Array.from(new Int32Array(buffer));
    default:
      throw new Error(`Unsupported dtype: ${dtype}`);
  }
};

export const useTimeseriesData = (dataset: Dataset) => {
  const [data, setData] = useState<number[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      if (!dataset.data_url_raw) {
        setError("No raw data URL available");
        return;
      }

      const metaJsonUrl = dataset.data_url_json;
      if (!metaJsonUrl) {
        setError("No JSON metadata URL available");
        return;
      }

      try {
        const metaResponse = await fetch(metaJsonUrl);
        if (!metaResponse.ok) {
          throw new Error(`HTTP error! status: ${metaResponse.status}`);
        }

        const metaJson = await metaResponse.json();

        const dtype = metaJson.dtype;
        const bytesPerElement = getDtypeSize(dtype);

        const numBytes = bytesPerElement * 1000;

        const response = await fetch(dataset.data_url_raw, {
          headers: {
            Range: `bytes=0-${numBytes - 1}`, // First 1000 elements
          },
        });

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const buffer = await response.arrayBuffer();
        const data = createTypedArray(buffer, dtype);
        setData(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to fetch data");
      }
    };
    fetchData();
  }, [dataset]);

  return { data, error };
};
