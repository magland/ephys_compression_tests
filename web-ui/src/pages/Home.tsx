import React, { useEffect, useState } from "react";
import axios from "axios";
import { Link } from "react-router-dom";
import yaml from "yaml";
import contentYaml from "../content/home-content.yml?raw";
import { HomeContent, HomeSection } from "../types/home-content";
import "../components/Button.css";

const content = yaml.parse(contentYaml) as HomeContent;

const SectionCard: React.FC<{ section: HomeSection }> = ({ section }) => {
  if (section.external) {
    return (
      <div
        style={{
          padding: "0.75rem",
          border: "1px solid #eaeaea",
          borderRadius: "8px",
          backgroundColor: "#f9f9f9",
          display: "flex",
          flexDirection: "column",
          height: "100%",
        }}
      >
        <h2 style={{ fontSize: "1.25rem", marginBottom: "0.5rem" }}>
          {section.title}
        </h2>
        <p style={{ marginBottom: "0.5rem" }}>{section.description}</p>
        <a
          href={section.link}
          target="_blank"
          rel="noopener noreferrer"
          className="soft-button"
          style={{ marginTop: "auto", alignSelf: "flex-start" }}
        >
          {section.linkText}
        </a>
      </div>
    );
  }

  return (
    <div
      style={{
        padding: "0.75rem",
        border: "1px solid #eaeaea",
        borderRadius: "8px",
        backgroundColor: "#f9f9f9",
        display: "flex",
        flexDirection: "column",
        height: "100%",
      }}
    >
      <h2 style={{ fontSize: "1.25rem", marginBottom: "0.5rem" }}>
        {section.title}
      </h2>
      <p style={{ marginBottom: "0.5rem" }}>{section.description}</p>
      <Link
        to={section.link}
        className="soft-button"
        style={{ marginTop: "auto", alignSelf: "flex-start" }}
      >
        {section.linkText}
      </Link>
    </div>
  );
};

interface BenchmarkStatus {
  current_dataset: string;
  current_algorithm: string;
  completed_count: number;
  total_count: number;
  progress_percentage: number;
  elapsed_time: number;
  last_update: string;
  completed_benchmarks: Array<{
    dataset: string;
    algorithm: string;
    compression_ratio: number;
    encode_time: number;
    decode_time: number;
    cache_status: string;
  }>;
}

export default function Home() {
  const [status, setStatus] = useState<BenchmarkStatus | null>(null);

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const cacheBust = Math.random().toString(36).substring(2, 15);
        const response = await axios.get(
          `https://tempory.net/f/memobin/ephys_compression_tests/benchmark_status/current.json?cachebust=${cacheBust}`,
        );
        setStatus(response.data);
      } catch (error) {
        console.error("Error fetching benchmark status:", error);
      }
    };

    fetchStatus();
  }, []);

  return (
    <div style={{ maxWidth: "1200px", margin: "0 auto", padding: "2rem" }}>
      <h1
        style={{
          marginBottom: "2rem",
          display: "flex",
          alignItems: "center",
          gap: "1rem",
        }}
      >
        <img
          src={`${import.meta.env.BASE_URL}logo.svg`}
          alt="Ephys Compression Tests Logo"
          style={{ width: "40px", height: "auto" }}
        />
        {content.title}
      </h1>

      <p
        style={{ fontSize: "1.1rem", lineHeight: "1.6", marginBottom: "2rem" }}
      >
        {content.description}
      </p>

      <div
        style={{
          display: "grid",
          gap: "2rem",
          gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))",
        }}
      >
        {Object.entries(content.sections).map(([key, section]) => (
          <SectionCard key={key} section={section} />
        ))}
      </div>

      <hr
        style={{
          margin: "3rem 0",
          border: "none",
          borderTop: "1px solid #eaeaea",
        }}
      />

      <footer
        style={{ textAlign: "center", color: "#666", fontSize: "0.9rem" }}
      >
        <p>
          Last UI update: {__BUILD_DATE__}
          <br />
          {status && (
            <>
              <div
                style={{
                  margin: "1rem 0",
                  padding: "0.5rem",
                  border: "1px solid #eaeaea",
                  borderRadius: "4px",
                  display: "inline-block",
                }}
              >
                Last benchmark run:{" "}
                {new Date(status.last_update).toLocaleString()}
                <br />
                Status:{" "}
                {status.progress_percentage === 100
                  ? "Completed"
                  : "In Progress"}{" "}
                ({status.completed_count}/{status.total_count} benchmarks)
              </div>
              <br />
            </>
          )}
          Released under{" "}
          <a
            href="https://github.com/magland/ephys_compression_tests/blob/main/LICENSE"
            target="_blank"
            rel="noopener noreferrer"
            style={{ color: "#666", textDecoration: "underline" }}
          >
            Apache License 2.0
          </a>
        </p>
      </footer>
    </div>
  );
}
