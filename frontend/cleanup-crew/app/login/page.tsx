"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useForm } from "react-hook-form";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/AuthContext";
import styles from "../auth.module.css";

interface LoginFields {
  email: string;
  password: string;
}

export default function LoginPage() {
  const router = useRouter();
  const { login } = useAuth();
  const [serverError, setServerError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginFields>();

  const onSubmit = async (data: LoginFields) => {
    setServerError(null);

    try {
      const response = await api.post("/auth/login", data);

      if (response.access_token) {
        login(response.access_token);
        router.push("/");
      }
    } catch (err) {
      setServerError(err instanceof Error ? err.message : "Login failed");
    }
  };

  return (
    <div className={styles.container}>
      <div className={styles.card}>
        <div className={styles.header}>
          <h1 className={styles.title}>Welcome Back</h1>
          <p className={styles.subtitle}>Log in to Cleanup Crew</p>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className={styles.form}>
          <div className={styles.formGroup}>
            <label htmlFor="email" className={styles.label}>
              Email
            </label>
            <input
              id="email"
              type="email"
              className={styles.input}
              disabled={isSubmitting}
              {...register("email", { required: "Email is required" })}
            />
            {errors.email && (
              <p className={styles.fieldError}>{errors.email.message}</p>
            )}
          </div>

          <div className={styles.formGroup}>
            <label htmlFor="password" className={styles.label}>
              Password
            </label>
            <input
              id="password"
              type="password"
              className={styles.input}
              disabled={isSubmitting}
              {...register("password", { required: "Password is required" })}
            />
            {errors.password && (
              <p className={styles.fieldError}>{errors.password.message}</p>
            )}
          </div>

          {serverError && (
            <div className={styles.errorBox}>
              <p className={styles.errorText}>{serverError}</p>
            </div>
          )}

          <button
            type="submit"
            disabled={isSubmitting}
            className={styles.submitButton}
          >
            {isSubmitting ? "Logging in..." : "Log In"}
          </button>
        </form>

        <div className={styles.footer}>
          <p className={styles.footerText}>
            Don&apos;t have an account?{" "}
            <Link href="/signup" className={styles.link}>
              Sign up
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
