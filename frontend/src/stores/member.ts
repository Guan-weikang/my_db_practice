import { defineStore } from "pinia";

export const useMemberStore = defineStore("member", {
  state: () => ({
    currentMemberId: null as number | null
  })
});

