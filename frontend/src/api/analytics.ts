import client from "./client";

export type DashboardSummary = {
  total_members: number;
  male_count: number;
  female_count: number;
  unknown_count: number;
  male_ratio: number | null;
  female_ratio: number | null;
};

export type DashboardResponse = {
  tree_id: number;
  summary: DashboardSummary;
};

export function fetchDashboard(treeId: number) {
  return client.get<DashboardResponse>(`/family-trees/${treeId}/analytics/dashboard`);
}
