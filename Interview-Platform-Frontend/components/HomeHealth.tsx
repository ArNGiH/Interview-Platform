"use client";

import { useEffect, useState } from "react";
import { getApiHealth } from "@/lib/api";

export function HomeHealth() {
  const [status, setStatus] = useState<"checking" | "online" | "offline">("checking");

  useEffect(() => {
    let mounted = true;

    getApiHealth()
      .then((response) => {
        if (mounted) {
          setStatus(response.status ? "online" : "offline");
        }
      })
      .catch(() => {
        if (mounted) {
          setStatus("offline");
        }
      });

    return () => {
      mounted = false;
    };
  }, []);

  const label =
    status === "checking"
      ? "Checking API"
      : status === "online"
        ? "API online"
        : "API offline";

  return (
    <span className="status-pill">
      <span
        className={`status-dot ${
          status === "online"
            ? "status-dot-online"
            : status === "offline"
              ? "status-dot-offline"
              : ""
        }`}
      />
      {label}
    </span>
  );
}
