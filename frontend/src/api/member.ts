import client from "./client";

export interface MemberListItem {
  member_id: number;
  tree_id: number;
  name: string;
  gender: "male" | "female" | "unknown";
  birth_date: string | null;
  death_date: string | null;
  is_alive: boolean;
  generation_no: number | null;
  generation_name: string | null;
}

export interface MemberDetailResponse extends MemberListItem {
  biography: string | null;
  created_at: string;
  updated_at: string;
}

export interface PaginatedMemberResponse {
  items: MemberListItem[];
  total: number;
  page: number;
  page_size: number;
}

export interface MemberCreatePayload {
  name: string;
  gender: "male" | "female" | "unknown";
  birth_date: string | null;
  death_date: string | null;
  is_alive: boolean;
  generation_no: number | null;
  generation_name: string | null;
  biography: string | null;
}

export interface MemberUpdatePayload {
  name?: string;
  gender?: "male" | "female" | "unknown";
  birth_date?: string | null;
  death_date?: string | null;
  is_alive?: boolean;
  generation_no?: number | null;
  generation_name?: string | null;
  biography?: string | null;
}

export function fetchMembers(treeId: number) {
  return client.get<PaginatedMemberResponse>(`/family-trees/${treeId}/members`);
}

export function fetchMemberDetail(treeId: number, memberId: number) {
  return client.get<MemberDetailResponse>(`/family-trees/${treeId}/members/${memberId}`);
}

export function createMember(treeId: number, payload: MemberCreatePayload) {
  return client.post<MemberDetailResponse>(`/family-trees/${treeId}/members`, payload);
}

export function updateMember(treeId: number, memberId: number, payload: MemberUpdatePayload) {
  return client.patch<MemberDetailResponse>(`/family-trees/${treeId}/members/${memberId}`, payload);
}

export function deleteMember(treeId: number, memberId: number) {
  return client.delete<{ message: string }>(`/family-trees/${treeId}/members/${memberId}`);
}
