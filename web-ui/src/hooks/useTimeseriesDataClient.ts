import { useEffect, useState } from "react";
import { Dataset } from "../types";
import { TimeseriesDataClient } from "./TimeseriesDataClient";

interface UseTimeseriesDataClientResult {
  client: TimeseriesDataClient | null;
  error: string | null;
}

export const useTimeseriesDataClient = (
  dataset: Dataset,
  chunkSize: number = 1000,
): UseTimeseriesDataClientResult => {
  const [client, setClient] = useState<TimeseriesDataClient | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const initClient = async () => {
      try {
        const newClient = await TimeseriesDataClient.create(
          dataset.data_url_json || "",
          dataset.data_url_raw || "",
          chunkSize,
        );
        setClient(newClient);
        setError(null);
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Failed to initialize client",
        );
        setClient(null);
      }
    };

    initClient();
  }, [dataset.data_url_json, dataset.data_url_raw, chunkSize]);

  return { client, error };
};
