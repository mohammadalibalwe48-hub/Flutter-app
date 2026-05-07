export type BuildState =
  | "queued"
  | "preparing"
  | "installing"
  | "building"
  | "ready"
  | "failed"
  | "cancelled";

export interface BuildSummary {
  id: string;
  state: BuildState;
  source_label: string;
  created_at: string;
  updated_at: string;
  preview_url: string | null;
  error: string | null;
}

export interface BuildDetail extends BuildSummary {
  logs: string;
  project_subdir: string | null;
}
