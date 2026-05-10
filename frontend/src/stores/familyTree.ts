import { defineStore } from "pinia";

export const useFamilyTreeStore = defineStore("familyTree", {
  state: () => ({
    currentTreeId: null as number | null
  }),
  actions: {
    setCurrentTree(treeId: number | null) {
      this.currentTreeId = treeId;
    }
  }
});

