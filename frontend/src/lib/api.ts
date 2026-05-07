import type { BuildDetail, BuildSummary } from "./types";

const TOKEN_KEY = "flutter-tester:token";
const BACKEND_KEY = "flutter-tester:backend-url";

export function getToken(): string {
  return localStorage.getItem(TOKEN_KEY) ?? "";
}

export function setToken(value: string): void {
  localStorage.setItem(TOKEN_KEY, value.trim());
}

function rawBackendUrl(): string {
  const override = localStorage.getItem(BACKEND_KEY);
  if (override) return override.replace(/\/$/, "");
  const fromEnv = (import.meta as unknown as { env?: { VITE_BACKEND_URL?: string } }).env
    ?.VITE_BACKEND_URL;
  if (fromEnv) return fromEnv.replace(/\/$/, "");
  return "";
}

interface ParsedBackend {
  origin: string; // scheme://host[:port], no trailing slash, no credentials
  basicAuth: string | null; // "user:pass" if URL contained credentials, else null
}

function parseBackend(): ParsedBackend {
  const raw = rawBackendUrl();
  if (!raw) return { origin: "", basicAuth: null };
  try {
    const u = new URL(raw);
    const basicAuth = u.username
      ? `${decodeURIComponent(u.username)}:${decodeURIComponent(u.password)}`
      : null;
    u.username = "";
    u.password = "";
    return { origin: u.toString().replace(/\/$/, ""), basicAuth };
  } catch {
    return { origin: raw, basicAuth: null };
  }
}

export function getBackendUrl(): string {
  return parseBackend().origin;
}

export function setBackendUrl(value: string): void {
  localStorage.setItem(BACKEND_KEY, value.trim().replace(/\/$/, ""));
}

function authHeaders(): HeadersInit {
  const headers: Record<string, string> = {};
  const token = getToken();
  if (token) headers["X-Tester-Token"] = token;
  const { basicAuth } = parseBackend();
  if (basicAuth) headers["Authorization"] = `Basic ${btoa(basicAuth)}`;
  return headers;
}

async function jsonOrThrow<T>(resp: Response): Promise<T> {
  if (!resp.ok) {
    const text = await resp.text().catch(() => "");
    throw new Error(`${resp.status} ${resp.statusText}: ${text || "request failed"}`);
  }
  return (await resp.json()) as T;
}

export async function createBuildFromGithub(input: {
  github_url: string;
  branch?: string;
  project_subdir?: string;
}): Promise<BuildSummary> {
  const resp = await fetch(`${getBackendUrl()}/api/builds`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify(input),
  });
  return jsonOrThrow<BuildSummary>(resp);
}

export async function createBuildFromZip(input: {
  file: File;
  project_subdir?: string;
}): Promise<BuildSummary> {
  const fd = new FormData();
  fd.append("file", input.file);
  if (input.project_subdir) fd.append("project_subdir", input.project_subdir);
  const resp = await fetch(`${getBackendUrl()}/api/builds/upload`, {
    method: "POST",
    headers: authHeaders(),
    body: fd,
  });
  return jsonOrThrow<BuildSummary>(resp);
}

export async function getBuild(id: string): Promise<BuildDetail> {
  const resp = await fetch(`${getBackendUrl()}/api/builds/${id}`, {
    headers: authHeaders(),
  });
  return jsonOrThrow<BuildDetail>(resp);
}

export async function listBuilds(): Promise<BuildSummary[]> {
  const resp = await fetch(`${getBackendUrl()}/api/builds`, {
    headers: authHeaders(),
  });
  return jsonOrThrow<BuildSummary[]>(resp);
}

export function previewUrl(buildId: string): string {
  // For iframes we cannot set request headers, so when the backend lives on a
  // different origin and uses basic auth we embed the credentials directly in
  // the URL. When the SPA is served from the same origin as the backend we
  // just return a relative URL (the iframe inherits cookies/basic-auth).
  const { origin, basicAuth } = parseBackend();
  if (!origin) return `/preview/${buildId}/`;
  if (basicAuth) {
    try {
      const u = new URL(`${origin}/preview/${buildId}/`);
      const [user, ...rest] = basicAuth.split(":");
      u.username = user;
      u.password = rest.join(":");
      return u.toString();
    } catch {
      // fall through
    }
  }
  return `${origin}/preview/${buildId}/`;
}
