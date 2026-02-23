const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL;

// Token management
export const getToken = (): string | null => {
    if (typeof window === "undefined") return null;
    return localStorage.getItem("access_token");
};

export const setToken = (token: string): void => {
    if (typeof window === "undefined") return;
    localStorage.setItem("access_token", token);
};

export const removeToken = (): void => {
    if (typeof window === "undefined") return;
    localStorage.removeItem("access_token");
};

// Base API fetch function
export async function apiFetch(
    endpoint: string,
    options: RequestInit = {}
) {
    const token = getToken();

    const res = await fetch(`${API_BASE_URL}${endpoint}`, {
        ...options,
        headers: {
            "Content-Type": "application/json",
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
            ...(options.headers || {}),
        },
    });

    if (!res.ok) {
        if (res.status === 401 && token) {
            removeToken();
            if (typeof window !== "undefined") {
                window.location.href = "/login";
            }
        }
        const error = await res.json().catch(() => null);
        throw new Error(error?.detail || "API request failed");
    }

    return res.json();
}

// Convenience methods
export const api = {
    get: (endpoint: string, options?: RequestInit) =>
        apiFetch(endpoint, { ...options, method: "GET" }),

    post: (endpoint: string, data?: unknown, options?: RequestInit) =>
        apiFetch(endpoint, {
            ...options,
            method: "POST",
            body: data ? JSON.stringify(data) : undefined,
        }),

    patch: (endpoint: string, data?: unknown, options?: RequestInit) =>
        apiFetch(endpoint, {
            ...options,
            method: "PATCH",
            body: data ? JSON.stringify(data) : undefined,
        }),

    delete: (endpoint: string, options?: RequestInit) =>
        apiFetch(endpoint, { ...options, method: "DELETE" }),
};
