import client from "./client";

export function fetchCollaborators(treeId: number) {
  return client.get(`/family-trees/${treeId}/collaborators`);
}

