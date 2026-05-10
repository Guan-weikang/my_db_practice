import client from "./client";

export function fetchParents(treeId: number, memberId: number) {
  return client.get(`/family-trees/${treeId}/relationships/members/${memberId}/parents`);
}

