import { defineStore } from "pinia";

import {
  createFamilyTree,
  fetchFamilyTreeDetail,
  fetchFamilyTrees,
  type FamilyTreeCreatePayload,
  type FamilyTreeDetailResponse,
  type FamilyTreeListItem,
  type FamilyTreeUpdatePayload,
  updateFamilyTree
} from "../api/familyTree";
import {
  fetchCollaborators,
  inviteCollaborator,
  revokeCollaborator,
  type CollaboratorCreatePayload,
  type CollaboratorItem,
  type CollaboratorUpdatePayload,
  updateCollaborator
} from "../api/collaborator";

export const useFamilyTreeStore = defineStore("familyTree", {
  state: () => ({
    currentTreeId: null as number | null,
    list: [] as FamilyTreeListItem[],
    currentTree: null as FamilyTreeDetailResponse | null,
    collaborators: [] as CollaboratorItem[],
    loadingList: false,
    loadingDetail: false,
    loadingCollaborators: false,
    errorMessage: ""
  }),
  actions: {
    setCurrentTree(treeId: number | null) {
      this.currentTreeId = treeId;
    },
    async loadFamilyTrees() {
      this.loadingList = true;
      try {
        const response = await fetchFamilyTrees();
        this.list = response.data.items;
      } finally {
        this.loadingList = false;
      }
    },
    async loadFamilyTreeDetail(treeId: number) {
      this.loadingDetail = true;
      this.currentTreeId = treeId;
      try {
        const response = await fetchFamilyTreeDetail(treeId);
        this.currentTree = response.data;
      } finally {
        this.loadingDetail = false;
      }
    },
    async createFamilyTree(payload: FamilyTreeCreatePayload) {
      const response = await createFamilyTree(payload);
      await this.loadFamilyTrees();
      return response.data;
    },
    async updateFamilyTree(treeId: number, payload: FamilyTreeUpdatePayload) {
      const response = await updateFamilyTree(treeId, payload);
      this.currentTree = response.data;
      this.list = this.list.map((tree) =>
        tree.tree_id === treeId
          ? {
              ...tree,
              tree_name: response.data.tree_name,
              surname: response.data.surname,
              compiled_at: response.data.compiled_at,
              description: response.data.description,
              access_role: response.data.access_role
            }
          : tree
      );
      await this.loadFamilyTrees();
      return response.data;
    },
    async loadCollaborators(treeId: number) {
      this.loadingCollaborators = true;
      try {
        const response = await fetchCollaborators(treeId);
        this.collaborators = response.data.items;
      } finally {
        this.loadingCollaborators = false;
      }
    },
    async inviteCollaborator(treeId: number, payload: CollaboratorCreatePayload) {
      const response = await inviteCollaborator(treeId, payload);
      await this.loadCollaborators(treeId);
      return response.data;
    },
    async updateCollaborator(treeId: number, userId: number, payload: CollaboratorUpdatePayload) {
      const response = await updateCollaborator(treeId, userId, payload);
      await this.loadCollaborators(treeId);
      return response.data;
    },
    async revokeCollaborator(treeId: number, userId: number) {
      const response = await revokeCollaborator(treeId, userId);
      await this.loadCollaborators(treeId);
      return response.data;
    }
  }
});
