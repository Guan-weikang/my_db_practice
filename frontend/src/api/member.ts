import client from "./client";

export function fetchMembers(treeId: number) {
  return client.get(`/family-trees/${treeId}/members`);
}

