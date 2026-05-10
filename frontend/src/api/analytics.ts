import client from "./client";

export function fetchDashboard(treeId: number) {
  return client.get(`/family-trees/${treeId}/analytics/dashboard`);
}

