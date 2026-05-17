import client from "./client";

export interface FamilyTreeListItem {
  tree_id: number;
  tree_name: string;
  surname: string;
  compiled_at: string | null;
  description: string | null;
  access_role: "creator" | "collaborator" | "reader";
}

export interface PaginatedFamilyTreeResponse {
  items: FamilyTreeListItem[];
  total: number;
  page: number;
  page_size: number;
}

export interface FamilyTreeDetailResponse {
  tree_id: number;
  tree_name: string;
  surname: string;
  compiled_at: string | null;
  description: string | null;
  access_role: "creator" | "collaborator" | "reader";
}

export interface FamilyTreeCreatePayload {
  tree_name: string;
  surname: string;
  compiled_at?: string | null;
  description?: string | null;
}

export interface FamilyTreeUpdatePayload {
  tree_name?: string;
  surname?: string;
  compiled_at?: string | null;
  description?: string | null;
}

export function fetchFamilyTrees(page = 1, pageSize = 20) {
  return client.get<PaginatedFamilyTreeResponse>("/family-trees/", {
    params: {
      page,
      page_size: pageSize
    }
  });
}

export function fetchFamilyTreeDetail(treeId: number) {
  return client.get<FamilyTreeDetailResponse>(`/family-trees/${treeId}`);
}

export function createFamilyTree(payload: FamilyTreeCreatePayload) {
  return client.post<FamilyTreeDetailResponse>("/family-trees/", payload);
}

export function updateFamilyTree(treeId: number, payload: FamilyTreeUpdatePayload) {
  return client.patch<FamilyTreeDetailResponse>(`/family-trees/${treeId}`, payload);
}
