import { BrowserRouter, Routes, Route, Link } from "react-router-dom";
import { useEffect, useState } from "react";
import axios from "axios";
import { ScrollToTop } from "./components/ScrollToTop";
import "./components/AppHeader.css";
import Home from "./pages/Home";
import BenchmarkView from "./pages/BenchmarkView";
import Monitor from "./pages/Monitor";
import Submit from "./pages/Submit";
import { BenchmarkData } from "./types";

function App() {
  const [benchmarkData, setBenchmarkData] = useState<BenchmarkData | null>(
    null,
  );
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setIsLoading(true);
        setError(null);
        const cacheBust = Math.random().toString(36).substring(2, 15);
        const response = await axios.get(
          `https://tempory.net/f/memobin/ephys_compression_tests/global/results.json?cachebust=${cacheBust}`,
        );
        setBenchmarkData(response.data);
      } catch (error) {
        const message =
          error instanceof Error ? error.message : "Failed to fetch data";
        setError(message);
        console.error("Error fetching benchmark data:", error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, []);

  return (
    <BrowserRouter basename="/ephys_compression_tests/">
      <ScrollToTop />
      <div
        style={{
          paddingTop: "3rem",
          padding: "3rem 2rem 2rem 2rem",
        }}
      >
        <nav
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            right: 0,
            padding: "0.35rem min(2rem, 4%)",
            backgroundColor: "white",
            zIndex: 1000,
          }}
        >
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              minHeight: "32px",
            }}
          >
            <Link
              to="/"
              style={{
                display: "flex",
                alignItems: "center",
                textDecoration: "none",
                minWidth: 0,
                maxWidth: "calc(100% - 80px)",
              }}
            >
              <img
                src="/ephys_compression_tests/logo.svg"
                alt="Ephys Compression Tests Logo"
                style={{
                  width: "28px",
                  height: "28px",
                  marginRight: "10px",
                  flexShrink: 0,
                }}
              />
              <span
                style={{
                  minWidth: 0,
                  whiteSpace: "nowrap",
                  overflow: "hidden",
                  textOverflow: "ellipsis",
                }}
              >
                <span
                  style={{
                    fontSize: "1rem",
                    fontWeight: "500",
                    color: "#2c2c2c",
                  }}
                >
                  Ephys Compression Tests
                </span>
                <span className="app-header-subtitle">
                  {" · "}
                  <span style={{ fontSize: "1rem", color: "#777" }}>
                    Comparing compression algorithms for ephys data
                  </span>
                </span>
              </span>
            </Link>
            <div style={{ display: "flex", gap: "1.5rem" }}>
              <Link
                to="/datasets"
                style={{
                  color: "#0066cc",
                  textDecoration: "none",
                  fontWeight: "500",
                }}
              >
                Datasets
              </Link>
              <Link
                to="/algorithms"
                style={{
                  color: "#0066cc",
                  textDecoration: "none",
                  fontWeight: "500",
                }}
              >
                Algorithms
              </Link>
            </div>
          </div>
        </nav>
        <main>
          {isLoading ? (
            <div>Loading benchmark data...</div>
          ) : error ? (
            <div>Error: {error}</div>
          ) : (
            <Routes>
              <Route path="/" element={<Home />} />
              <Route
                path="/datasets"
                element={<BenchmarkView benchmarkData={benchmarkData} />}
              />
              <Route
                path="/algorithms"
                element={<BenchmarkView benchmarkData={benchmarkData} />}
              />
              <Route
                path="/dataset/:datasetName"
                element={<BenchmarkView benchmarkData={benchmarkData} />}
              />
              <Route
                path="/algorithm/:algorithmName"
                element={<BenchmarkView benchmarkData={benchmarkData} />}
              />
              <Route path="/monitor" element={<Monitor />} />
              <Route path="/submit" element={<Submit />} />
            </Routes>
          )}
        </main>
      </div>
    </BrowserRouter>
  );
}

export default App;
