import { useLocation, useNavigate, useParams } from "react-router-dom";
import { useReducer, useEffect } from "react";
import { tabsReducer } from "../reducers/tabsReducer";
import { AlgorithmContent } from "../components/algorithm/AlgorithmContent";
import { DatasetContent } from "../components/dataset/DatasetContent";
import {
  AlgorithmTable,
  DatasetTable,
} from "../components/tables/DatasetAlgorithmTables";
import { useBenchmarkChartData } from "../hooks/useBenchmarkChartData";
import { useTagFilter } from "../hooks/useTagFilter";
import { BenchmarkData } from "../types";

interface BenchmarkViewProps {
  benchmarkData: BenchmarkData | null;
}

export default function BenchmarkView({ benchmarkData }: BenchmarkViewProps) {
  const location = useLocation();
  const navigate = useNavigate();
  const { datasetName, algorithmName } = useParams<{
    datasetName?: string;
    algorithmName?: string;
  }>();

  const [tabsState, dispatch] = useReducer(tabsReducer, {
    tabs: [
      { id: "datasets", label: "Datasets", route: "/datasets" },
      { id: "algorithms", label: "Algorithms", route: "/algorithms" },
    ],
    activeTabId: "datasets",
  });

  // Effect to handle URL changes and update tabs
  useEffect(() => {
    if (datasetName) {
      dispatch({
        type: "ADD_TAB",
        payload: {
          id: `dataset-${datasetName}`,
          label: datasetName,
          route: `/dataset/${datasetName}`,
        },
      });
    } else if (algorithmName) {
      dispatch({
        type: "ADD_TAB",
        payload: {
          id: `algorithm-${algorithmName}`,
          label: algorithmName,
          route: `/algorithm/${algorithmName}`,
        },
      });
    } else if (location.pathname.includes("/algorithms")) {
      dispatch({ type: "SET_ACTIVE_TAB", payload: "algorithms" });
    } else if (location.pathname.includes("/datasets")) {
      dispatch({ type: "SET_ACTIVE_TAB", payload: "datasets" });
    }
  }, [datasetName, algorithmName, location.pathname]);

  // Handle tab click
  const handleTabClick = (tabId: string, route: string) => {
    dispatch({ type: "SET_ACTIVE_TAB", payload: tabId });
    navigate(route);
  };

  // Get specific dataset or algorithm if viewing one
  const dataset = datasetName
    ? benchmarkData?.datasets.find((d) => d.name === datasetName)
    : undefined;
  const algorithm = algorithmName
    ? benchmarkData?.algorithms.find((a) => a.name === algorithmName)
    : undefined;

  // Get chart data for specific dataset or algorithm view
  const chartData = useBenchmarkChartData(
    benchmarkData?.results || [],
    dataset?.name || null,
    algorithm?.name || null,
  );

  // Get selected tags from URL
  const searchParams = new URLSearchParams(location.search);
  const selectedTags = searchParams.get("tag")?.split(",") || [];

  // Set up tag filtering for datasets and algorithms
  const {
    availableTags: availableDatasetTags,
    filteredItems: filteredDatasets,
  } = useTagFilter(
    benchmarkData?.datasets || [],
    location.pathname.includes("/datasets") ? selectedTags : [],
  );

  const {
    availableTags: availableAlgorithmTags,
    filteredItems: filteredAlgorithms,
  } = useTagFilter(
    benchmarkData?.algorithms || [],
    location.pathname.includes("/algorithms") ? selectedTags : [],
  );

  // Handle tag toggling by updating URL
  const handleTagToggle = (tag: string) => {
    const newTags = selectedTags.includes(tag)
      ? selectedTags.filter((t) => t !== tag)
      : [...selectedTags, tag];

    const params = new URLSearchParams();
    if (newTags.length > 0) {
      params.set("tag", newTags.join(","));
    }
    navigate({ search: params.toString() });
  };

  return (
    <div>
      <main>
        <div
          style={{
            position: "fixed",
            top: "3rem",
            left: 0,
            right: 0,
            backgroundColor: "white",
            zIndex: 999,
            padding: "0 2rem 0 2rem",
            marginTop: "-4px",
            boxShadow: "0 2px 4px rgba(0,0,0,0.1)",
            borderBottom: "1px solid #eaeaea",
          }}
        >
          <div
            style={{
              paddingBottom: "2px",
              display: "flex",
              gap: "4px",
              overflowX: "auto",
              width: "100%",
              backgroundColor: "white",
            }}
          >
            {tabsState.tabs.map((tab) => (
              <div
                key={tab.id}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "4px",
                }}
              >
                <button
                  onClick={() => handleTabClick(tab.id, tab.route)}
                  style={{
                    padding: "8px 16px",
                    border: "none",
                    background: "none",
                    borderBottom:
                      tabsState.activeTabId === tab.id
                        ? "2px solid #0066cc"
                        : "none",
                    color:
                      tabsState.activeTabId === tab.id ? "#0066cc" : "#666",
                    fontWeight:
                      tabsState.activeTabId === tab.id ? "600" : "normal",
                    cursor: "pointer",
                    textDecoration: "none",
                    whiteSpace: "nowrap",
                  }}
                >
                  {tab.label}
                </button>
                {tab.id !== "datasets" && tab.id !== "algorithms" && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      const newActiveTab =
                        tab.id === tabsState.activeTabId
                          ? tabsState.tabs[0].id // Default to first tab if closing active
                          : tabsState.activeTabId;
                      dispatch({ type: "CLOSE_TAB", payload: tab.id });
                      // Navigate if closing active tab
                      if (tab.id === tabsState.activeTabId) {
                        const defaultTab = tabsState.tabs.find(
                          (t) => t.id === newActiveTab,
                        );
                        if (defaultTab) {
                          navigate(defaultTab.route);
                        }
                      }
                    }}
                    style={{
                      padding: "4px",
                      border: "none",
                      background: "none",
                      color: "#666",
                      cursor: "pointer",
                      fontSize: "12px",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      width: "20px",
                      height: "20px",
                      borderRadius: "50%",
                      marginRight: "4px",
                      marginLeft: "-4px",
                    }}
                    aria-label="Close tab"
                  >
                    ×
                  </button>
                )}
              </div>
            ))}
          </div>
        </div>

        <div style={{ padding: "3rem 0 1rem 0" }}>
          {dataset ? (
            <DatasetContent
              dataset={dataset}
              benchmarkData={benchmarkData}
              chartData={chartData}
            />
          ) : algorithm ? (
            <AlgorithmContent
              algorithm={algorithm}
              benchmarkData={benchmarkData}
              chartData={chartData}
            />
          ) : tabsState.activeTabId === "datasets" ? (
            <DatasetTable
              filteredDatasets={filteredDatasets}
              availableDatasetTags={availableDatasetTags}
              selectedTags={selectedTags}
              toggleTag={handleTagToggle}
              benchmarkResults={benchmarkData?.results || []}
            />
          ) : (
            <AlgorithmTable
              filteredAlgorithms={filteredAlgorithms}
              availableAlgorithmTags={availableAlgorithmTags}
              selectedTags={selectedTags}
              toggleTag={handleTagToggle}
            />
          )}
        </div>
      </main>
    </div>
  );
}
