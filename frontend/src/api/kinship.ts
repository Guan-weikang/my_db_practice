import client from "./client";
import type { MemberGraphNode } from "./search";

export interface AncestorNode extends MemberGraphNode {
  depth: number;
  child_member_id: number;
  parent_role: "father" | "mother";
  path_member_ids: number[];
}

export interface AncestorResponse {
  start_member: MemberGraphNode;
  max_depth: number;
  nodes: AncestorNode[];
}

export interface KinshipPathEdge {
  from_member_id: number;
  to_member_id: number;
  relation_type: "parent" | "child" | "spouse";
  parent_role: "father" | "mother" | null;
  marriage_status: "active" | "ended" | null;
}

export interface KinshipPathResponse {
  exists: boolean;
  hop_count: number | null;
  nodes: MemberGraphNode[];
  edges: KinshipPathEdge[];
}

export function fetchAncestors(treeId: number, memberId: number, maxDepth = 30) {
  return client.get<AncestorResponse>(`/family-trees/${treeId}/kinship/ancestors/${memberId}`, {
    params: { max_depth: maxDepth }
  });
}

export function fetchKinshipPath(
  treeId: number,
  memberA: number,
  memberB: number,
  maxDepth = 12,
  includeEndedMarriages = false
) {
  return client.get<KinshipPathResponse>(`/family-trees/${treeId}/kinship/path`, {
    params: {
      member_a: memberA,
      member_b: memberB,
      max_depth: maxDepth,
      include_ended_marriages: includeEndedMarriages
    }
  });
}
