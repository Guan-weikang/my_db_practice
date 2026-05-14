import client from "./client";

export interface SearchMemberItem {
  member_id: number;
  tree_id: number;
  name: string;
  gender: "male" | "female" | "unknown";
  birth_date: string | null;
  death_date: string | null;
  is_alive: boolean;
  generation_no: number | null;
  generation_name: string | null;
  father_name: string | null;
  mother_name: string | null;
}

export interface PaginatedSearchMemberResponse {
  items: SearchMemberItem[];
  total: number;
  page: number;
  page_size: number;
}

export interface MemberGraphNode {
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

export interface BranchTreeNode extends MemberGraphNode {
  depth: number;
  parent_member_id: number | null;
  incoming_parent_role: "father" | "mother" | null;
  path_member_ids: number[];
}

export interface BranchTreeResponse {
  root_member: MemberGraphNode;
  max_depth: number;
  nodes: BranchTreeNode[];
}

export function searchMembers(treeId: number, keyword: string, page = 1, pageSize = 20) {
  return client.get<PaginatedSearchMemberResponse>(`/family-trees/${treeId}/search/members`, {
    params: { keyword, page, page_size: pageSize }
  });
}

export function fetchBranchTree(treeId: number, rootMemberId: number, maxDepth = 4) {
  return client.get<BranchTreeResponse>(`/family-trees/${treeId}/search/branch-tree`, {
    params: { root_member_id: rootMemberId, max_depth: maxDepth }
  });
}
