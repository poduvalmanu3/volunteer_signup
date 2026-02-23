"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useForm } from "react-hook-form";
import { api } from "@/lib/api";
import styles from "../auth.module.css";
import signupStyles from "./page.module.css";

const MIN_PASSWORD_LENGTH = 8;

interface SignupFields {
  name: string;
  email: string;
  password: string;
}

export default function SignupPage() {
  const router = useRouter();
  const [serverError, setServerError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const redirectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<SignupFields>();

  useEffect(() => {
    return () => {
      if (redirectTimerRef.current) {
        clearTimeout(redirectTimerRef.current);
      }
    };
  }, []);

  const onSubmit = async (data: SignupFields) => {
    setServerError(null);

    try {
      await api.post("/auth/signup", data);
      setSuccess(true);

      redirectTimerRef.current = setTimeout(() => {
        router.push("/login");
      }, 2000);
    } catch (err) {
      setServerError(err instanceof Error ? err.message : "Signup failed");
    }
  };

  return (
    <div className={styles.container}>
      <div className={styles.card}>
        <div className={styles.header}>
          <h1 className={styles.title}>Create Account</h1>
          <p className={styles.subtitle}>Sign up for Cleanup Crew</p>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className={styles.form}>
          <div className={styles.formGroup}>
            <label htmlFor="name" className={styles.label}>
              Name
            </label>
            <input
              id="name"
              type="text"
              className={styles.input}
              disabled={isSubmitting}
              {...register("name", { required: "Name is required" })}
            />
            {errors.name && (
              <p className={styles.fieldError}>{errors.name.message}</p>
            )}
          </div>

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
              {...register("password", {
                required: "Password is required",
                minLength: {
                  value: MIN_PASSWORD_LENGTH,
                  message: `Minimum ${MIN_PASSWORD_LENGTH} characters`,
                },
              })}
            />
            {errors.password ? (
              <p className={styles.fieldError}>{errors.password.message}</p>
            ) : (
              <p className={signupStyles.hint}>
                Minimum {MIN_PASSWORD_LENGTH} characters
              </p>
            )}
          </div>

          {serverError && (
            <div className={styles.errorBox}>
              <p className={styles.errorText}>{serverError}</p>
            </div>
          )}

          {success && (
            <div className={signupStyles.successBox}>
              <p className={signupStyles.successText}>
                Account created successfully! Redirecting to login...
              </p>
            </div>
          )}

          <button
            type="submit"
            disabled={isSubmitting || success}
            className={styles.submitButton}
          >
            {isSubmitting ? "Creating account..." : "Sign Up"}
          </button>
        </form>

        <div className={styles.footer}>
          <p className={styles.footerText}>
            Already have an account?{" "}
            <Link href="/login" className={styles.link}>
              Log in
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
