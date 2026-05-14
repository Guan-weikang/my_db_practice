import { defineStore } from "pinia";

const CURRENT_TREE_ID_KEY = "family-tree.currentTreeId";

export const useAppStore = defineStore("app", {
  state: () => ({
    loading: false,
    currentTreeId: readStoredTreeId()
  }),
  actions: {
    setCurrentTreeId(treeId: number | null) {
      this.currentTreeId = treeId;

      if (treeId === null) {
        window.localStorage.removeItem(CURRENT_TREE_ID_KEY);
        return;
      }

      window.localStorage.setItem(CURRENT_TREE_ID_KEY, String(treeId));
    }
  }
});

function readStoredTreeId() {
  const rawValue = window.localStorage.getItem(CURRENT_TREE_ID_KEY);
  if (!rawValue) {
    return null;
  }

  const treeId = Number(rawValue);
  return Number.isFinite(treeId) && treeId > 0 ? treeId : null;
}
