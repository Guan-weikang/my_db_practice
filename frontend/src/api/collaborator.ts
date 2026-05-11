import client from "./client";

export interface CollaboratorItem {
  user_id: number;
  username: string;
  display_name: string | null;
  access_role: "collaborator" | "reader";
  status: "active" | "revoked" | "pending";
  invited_by: number;
  invited_at: string;
}

export interface PaginatedCollaboratorResponse {
  items: CollaboratorItem[];
  total: number;
  page: number;
  page_size: number;
}

export interface CollaboratorCreatePayload {
  user_id: number;
  access_role: "collaborator" | "reader";
}

export interface CollaboratorUpdatePayload {
  access_role: "collaborator" | "reader";
}

export function fetchCollaborators(treeId: number, page = 1, pageSize = 20) {
  return client.get<PaginatedCollaboratorResponse>(`/family-trees/${treeId}/collaborators`, {
    params: {
      page,
      page_size: pageSize
    }
  });
}

export function inviteCollaborator(treeId: number, payload: CollaboratorCreatePayload) {
  return client.post<CollaboratorItem>(`/family-trees/${treeId}/collaborators`, payload);
}

export function updateCollaborator(treeId: number, userId: number, payload: CollaboratorUpdatePayload) {
  return client.patch<CollaboratorItem>(`/family-trees/${treeId}/collaborators/${userId}`, payload);
}

export function revokeCollaborator(treeId: number, userId: number) {
  return client.delete<{ message: string }>(`/family-trees/${treeId}/collaborators/${userId}`);
}
