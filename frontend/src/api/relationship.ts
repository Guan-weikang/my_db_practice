import client from "./client";

export interface ParentRelationItem {
  parent_member_id: number;
  parent_role: "father" | "mother";
  name: string;
  gender: "male" | "female" | "unknown";
  birth_date: string | null;
  death_date: string | null;
  generation_no: number | null;
  generation_name: string | null;
}

export interface ChildRelationItem {
  child_member_id: number;
  parent_role: "father" | "mother";
  name: string;
  gender: "male" | "female" | "unknown";
  birth_date: string | null;
  death_date: string | null;
  generation_no: number | null;
  generation_name: string | null;
}

export interface SpouseRelationItem {
  spouse_member_id: number;
  name: string;
  gender: "male" | "female" | "unknown";
  birth_date: string | null;
  death_date: string | null;
  generation_no: number | null;
  generation_name: string | null;
  married_at: string | null;
  ended_at: string | null;
  status: "active" | "ended";
}

export interface ParentChildPayload {
  parent_member_id: number;
  child_member_id: number;
  parent_role: "father" | "mother";
}

export interface MarriagePayload {
  member_id_1: number;
  member_id_2: number;
  married_at?: string | null;
  ended_at?: string | null;
  status?: "active" | "ended";
}

export function fetchParents(treeId: number, memberId: number) {
  return client.get<ParentRelationItem[]>(`/family-trees/${treeId}/relationships/members/${memberId}/parents`);
}

export function fetchChildren(treeId: number, memberId: number) {
  return client.get<ChildRelationItem[]>(`/family-trees/${treeId}/relationships/members/${memberId}/children`);
}

export function fetchSpouses(treeId: number, memberId: number) {
  return client.get<SpouseRelationItem[]>(`/family-trees/${treeId}/relationships/members/${memberId}/spouses`);
}

export function createParentChild(treeId: number, payload: ParentChildPayload) {
  return client.post(`/family-trees/${treeId}/relationships/parent-child`, payload);
}

export function deleteParentChild(treeId: number, payload: ParentChildPayload) {
  return client.request<{ message: string }>({
    method: "DELETE",
    url: `/family-trees/${treeId}/relationships/parent-child`,
    data: payload
  });
}

export function createMarriage(treeId: number, payload: MarriagePayload) {
  return client.post(`/family-trees/${treeId}/relationships/marriages`, payload);
}

export function updateMarriage(treeId: number, payload: MarriagePayload) {
  return client.patch(`/family-trees/${treeId}/relationships/marriages`, payload);
}

export function deleteMarriage(treeId: number, payload: Pick<MarriagePayload, "member_id_1" | "member_id_2">) {
  return client.request<{ message: string }>({
    method: "DELETE",
    url: `/family-trees/${treeId}/relationships/marriages`,
    data: payload
  });
}
