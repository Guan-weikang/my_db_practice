import { createRouter, createWebHistory, type RouteRecordRaw } from "vue-router";

import AuthLayout from "../layouts/AuthLayout.vue";
import DefaultLayout from "../layouts/DefaultLayout.vue";
import { useAuthStore } from "../stores/auth";
import { pinia } from "../stores/pinia";
import LoginView from "../views/auth/LoginView.vue";
import RegisterView from "../views/auth/RegisterView.vue";
import DashboardView from "../views/dashboard/DashboardView.vue";
import FamilyTreeDetailView from "../views/family-tree/FamilyTreeDetailView.vue";
import FamilyTreeListView from "../views/family-tree/FamilyTreeListView.vue";
import MemberDetailView from "../views/member/MemberDetailView.vue";
import MemberListView from "../views/member/MemberListView.vue";
import AncestorQueryView from "../views/query/AncestorQueryView.vue";
import BranchTreeView from "../views/query/BranchTreeView.vue";
import KinshipQueryView from "../views/query/KinshipQueryView.vue";
import MemberSearchView from "../views/query/MemberSearchView.vue";
import CollaboratorManageView from "../views/collaboration/CollaboratorManageView.vue";

const routes: RouteRecordRaw[] = [
  {
    path: "/auth",
    component: AuthLayout,
    children: [
      { path: "", redirect: { name: "login" } },
      { path: "login", name: "login", component: LoginView, meta: { guestOnly: true } },
      { path: "register", name: "register", component: RegisterView, meta: { guestOnly: true } }
    ]
  },
  {
    path: "/",
    component: DefaultLayout,
    meta: { requiresAuth: true },
    children: [
      { path: "", name: "dashboard", component: DashboardView },
      { path: "family-trees", name: "family-tree-list", component: FamilyTreeListView },
      { path: "family-trees/:treeId", name: "family-tree-detail", component: FamilyTreeDetailView },
      { path: "family-trees/:treeId/collaborators", name: "collaborators", component: CollaboratorManageView },
      { path: "family-trees/:treeId/members", name: "member-list", component: MemberListView },
      { path: "family-trees/:treeId/members/:memberId", name: "member-detail", component: MemberDetailView },
      { path: "family-trees/:treeId/query/search", name: "member-search", component: MemberSearchView },
      { path: "family-trees/:treeId/query/branch-tree", name: "branch-tree", component: BranchTreeView },
      { path: "family-trees/:treeId/query/ancestors", name: "ancestor-query", component: AncestorQueryView },
      { path: "family-trees/:treeId/query/kinship", name: "kinship-query", component: KinshipQueryView }
    ]
  }
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

router.beforeEach(async (to) => {
  const authStore = useAuthStore(pinia);
  await authStore.initialize();

  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    return {
      name: "login",
      query: {
        redirect: to.fullPath
      }
    };
  }

  if (to.meta.guestOnly && authStore.isAuthenticated) {
    const redirect = typeof to.query.redirect === "string" ? to.query.redirect : "/";
    return redirect;
  }

  return true;
});

export default router;
