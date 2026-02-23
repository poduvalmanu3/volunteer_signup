"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/AuthContext";
import styles from "./page.module.css";

export default function Home() {
  const router = useRouter();
  const { isAuthenticated } = useAuth();
  const [healthStatus, setHealthStatus] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isAuthenticated) {
      router.replace("/login");
    }
  }, [isAuthenticated, router]);

  const testHealthEndpoint = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.get("/health");
      setHealthStatus(JSON.stringify(response, null, 2));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.container}>
      <main className={styles.main}>
        <div className={styles.header}>
          <h1 className={styles.title}>Cleanup Crew</h1>
          <p className={styles.subtitle}>
            Community-driven neighborhood cleanup activities
          </p>
        </div>

        <div className={styles.content}>
          <button
            onClick={testHealthEndpoint}
            disabled={loading}
            className={styles.testButton}
          >
            {loading ? "Testing..." : "Test API Connection"}
          </button>

          {healthStatus && (
            <div className={styles.successBox}>
              <p className={styles.successTitle}>✓ API Connected</p>
              <pre className={styles.successContent}>{healthStatus}</pre>
            </div>
          )}

          {error && (
            <div className={styles.errorBox}>
              <p className={styles.errorTitle}>✗ Connection Failed</p>
              <p className={styles.errorContent}>{error}</p>
            </div>
          )}

          <div className={styles.footer}>
            <p>Backend: {process.env.NEXT_PUBLIC_API_BASE_URL || "Not configured"}</p>
          </div>
        </div>
      </main>
    </div>
  );
}
