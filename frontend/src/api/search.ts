import client from "./client";

export function searchMembers(treeId: number, keyword: string) {
  return client.get(`/family-trees/${treeId}/search/members`, { params: { keyword } });
}

