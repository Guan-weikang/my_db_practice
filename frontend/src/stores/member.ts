import { defineStore } from "pinia";

import {
  createMember,
  deleteMember,
  fetchMemberDetail,
  fetchMembers,
  type MemberCreatePayload,
  type MemberDetailResponse,
  type MemberListItem,
  type MemberUpdatePayload,
  updateMember
} from "../api/member";
import {
  createMarriage,
  createParentChild,
  deleteMarriage,
  deleteParentChild,
  fetchChildren,
  fetchParents,
  fetchSpouses,
  type ChildRelationItem,
  type MarriagePayload,
  type ParentChildPayload,
  type ParentRelationItem,
  type SpouseRelationItem,
  updateMarriage
} from "../api/relationship";

export const useMemberStore = defineStore("member", {
  state: () => ({
    currentMemberId: null as number | null,
    list: [] as MemberListItem[],
    currentMember: null as MemberDetailResponse | null,
    parents: [] as ParentRelationItem[],
    children: [] as ChildRelationItem[],
    spouses: [] as SpouseRelationItem[],
    total: 0,
    page: 1,
    pageSize: 20,
    loadingList: false,
    loadingDetail: false,
    loadingRelations: false
  }),
  actions: {
    async loadMembers(treeId: number, page = 1, pageSize = 20) {
      this.loadingList = true;
      try {
        const response = await fetchMembers(treeId, page, pageSize);
        this.list = response.data.items;
        this.total = response.data.total;
        this.page = response.data.page;
        this.pageSize = response.data.page_size;
      } finally {
        this.loadingList = false;
      }
    },
    async loadMemberDetail(treeId: number, memberId: number) {
      this.loadingDetail = true;
      this.currentMemberId = memberId;
      try {
        const response = await fetchMemberDetail(treeId, memberId);
        this.currentMember = response.data;
      } finally {
        this.loadingDetail = false;
      }
    },
    async loadRelationships(treeId: number, memberId: number) {
      this.loadingRelations = true;
      try {
        const [parentsResponse, childrenResponse, spousesResponse] = await Promise.all([
          fetchParents(treeId, memberId),
          fetchChildren(treeId, memberId),
          fetchSpouses(treeId, memberId)
        ]);
        this.parents = parentsResponse.data;
        this.children = childrenResponse.data;
        this.spouses = spousesResponse.data;
      } finally {
        this.loadingRelations = false;
      }
    },
    async createMember(treeId: number, payload: MemberCreatePayload) {
      const response = await createMember(treeId, payload);
      await this.loadMembers(treeId, this.page, this.pageSize);
      return response.data;
    },
    async updateMember(treeId: number, memberId: number, payload: MemberUpdatePayload) {
      const response = await updateMember(treeId, memberId, payload);
      this.currentMember = response.data;
      await this.loadMembers(treeId, this.page, this.pageSize);
      return response.data;
    },
    async deleteMember(treeId: number, memberId: number) {
      const response = await deleteMember(treeId, memberId);
      await this.loadMembers(treeId, this.page, this.pageSize);
      if (this.currentMemberId === memberId) {
        this.currentMember = null;
        this.parents = [];
        this.children = [];
        this.spouses = [];
      }
      return response.data;
    },
    async createParentChild(treeId: number, payload: ParentChildPayload) {
      const response = await createParentChild(treeId, payload);
      await this.loadRelationships(treeId, payload.child_member_id);
      if (this.currentMemberId === payload.parent_member_id) {
        await this.loadRelationships(treeId, payload.parent_member_id);
      }
      return response.data;
    },
    async deleteParentChild(treeId: number, payload: ParentChildPayload) {
      const response = await deleteParentChild(treeId, payload);
      await this.loadRelationships(treeId, payload.child_member_id);
      if (this.currentMemberId === payload.parent_member_id) {
        await this.loadRelationships(treeId, payload.parent_member_id);
      }
      return response.data;
    },
    async createMarriage(treeId: number, payload: MarriagePayload) {
      const response = await createMarriage(treeId, payload);
      if (this.currentMemberId === payload.member_id_1 || this.currentMemberId === payload.member_id_2) {
        await this.loadRelationships(treeId, this.currentMemberId);
      }
      return response.data;
    },
    async updateMarriage(treeId: number, payload: MarriagePayload) {
      const response = await updateMarriage(treeId, payload);
      if (this.currentMemberId === payload.member_id_1 || this.currentMemberId === payload.member_id_2) {
        await this.loadRelationships(treeId, this.currentMemberId);
      }
      return response.data;
    },
    async deleteMarriage(treeId: number, payload: Pick<MarriagePayload, "member_id_1" | "member_id_2">) {
      const response = await deleteMarriage(treeId, payload);
      if (this.currentMemberId === payload.member_id_1 || this.currentMemberId === payload.member_id_2) {
        await this.loadRelationships(treeId, this.currentMemberId);
      }
      return response.data;
    }
  }
});
