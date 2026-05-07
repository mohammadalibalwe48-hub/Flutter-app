import { useState } from "react";

export type SubmitInput =
  | { kind: "github"; github_url: string; branch?: string; project_subdir?: string }
  | { kind: "zip"; file: File; project_subdir?: string };

interface Props {
  onSubmit: (input: SubmitInput) => Promise<void> | void;
  busy: boolean;
}

export function SubmitForm({ onSubmit, busy }: Props): JSX.Element {
  const [tab, setTab] = useState<"github" | "zip">("github");
  const [githubUrl, setGithubUrl] = useState("");
  const [branch, setBranch] = useState("");
  const [subdir, setSubdir] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handle = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    try {
      if (tab === "github") {
        if (!githubUrl) {
          setError("GitHub URL is required.");
          return;
        }
        await onSubmit({
          kind: "github",
          github_url: githubUrl.trim(),
          branch: branch.trim() || undefined,
          project_subdir: subdir.trim() || undefined,
        });
      } else {
        if (!file) {
          setError("Choose a .zip file.");
          return;
        }
        await onSubmit({ kind: "zip", file, project_subdir: subdir.trim() || undefined });
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  };

  return (
    <form onSubmit={handle} className="space-y-3">
      <div className="flex gap-2 text-xs">
        <button
          type="button"
          onClick={() => setTab("github")}
          className={`rounded-full px-3 py-1 ${tab === "github" ? "bg-sky-600 text-white" : "bg-neutral-800 text-neutral-300"}`}
        >
          GitHub URL
        </button>
        <button
          type="button"
          onClick={() => setTab("zip")}
          className={`rounded-full px-3 py-1 ${tab === "zip" ? "bg-sky-600 text-white" : "bg-neutral-800 text-neutral-300"}`}
        >
          Upload .zip
        </button>
      </div>

      {tab === "github" ? (
        <>
          <label className="block text-sm">
            <span className="mb-1 block text-neutral-400">Public GitHub repo URL</span>
            <input
              value={githubUrl}
              onChange={(e) => setGithubUrl(e.target.value)}
              placeholder="https://github.com/owner/repo"
              className="w-full rounded border border-neutral-700 bg-neutral-950 px-3 py-2 text-sm focus:border-sky-500 focus:outline-none"
            />
          </label>
          <label className="block text-sm">
            <span className="mb-1 block text-neutral-400">Branch (optional)</span>
            <input
              value={branch}
              onChange={(e) => setBranch(e.target.value)}
              placeholder="main"
              className="w-full rounded border border-neutral-700 bg-neutral-950 px-3 py-2 text-sm focus:border-sky-500 focus:outline-none"
            />
          </label>
        </>
      ) : (
        <label className="block text-sm">
          <span className="mb-1 block text-neutral-400">.zip of your Flutter project</span>
          <input
            type="file"
            accept=".zip"
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            className="w-full text-sm text-neutral-300 file:mr-3 file:rounded file:border-0 file:bg-neutral-800 file:px-3 file:py-2 file:text-sm file:text-neutral-100"
          />
        </label>
      )}

      <label className="block text-sm">
        <span className="mb-1 block text-neutral-400">
          Project subdir (only if pubspec.yaml is not at root)
        </span>
        <input
          value={subdir}
          onChange={(e) => setSubdir(e.target.value)}
          placeholder="apps/my_app"
          className="w-full rounded border border-neutral-700 bg-neutral-950 px-3 py-2 text-sm focus:border-sky-500 focus:outline-none"
        />
      </label>

      {error && <p className="text-xs text-rose-400">{error}</p>}

      <button
        type="submit"
        disabled={busy}
        className="w-full rounded bg-sky-600 py-2 text-sm font-medium text-white hover:bg-sky-500 disabled:cursor-not-allowed disabled:opacity-60"
      >
        {busy ? "Working…" : "Build & run"}
      </button>
    </form>
  );
}
