import { createRouter, createWebHistory, type RouteRecordRaw } from "vue-router";

import AuthLayout from "../layouts/AuthLayout.vue";
import DefaultLayout from "../layouts/DefaultLayout.vue";
import LoginView from "../views/auth/LoginView.vue";
import RegisterView from "../views/auth/RegisterView.vue";
import DashboardView from "../views/dashboard/DashboardView.vue";
import FamilyTreeDetailView from "../views/family-tree/FamilyTreeDetailView.vue";
import FamilyTreeListView from "../views/family-tree/FamilyTreeListView.vue";
import MemberDetailView from "../views/member/MemberDetailView.vue";
import MemberListView from "../views/member/MemberListView.vue";
import AncestorQueryView from "../views/query/AncestorQueryView.vue";
import KinshipQueryView from "../views/query/KinshipQueryView.vue";
import CollaboratorManageView from "../views/collaboration/CollaboratorManageView.vue";

const routes: RouteRecordRaw[] = [
  {
    path: "/auth",
    component: AuthLayout,
    children: [
      { path: "login", component: LoginView },
      { path: "register", component: RegisterView }
    ]
  },
  {
    path: "/",
    component: DefaultLayout,
    children: [
      { path: "", component: DashboardView },
      { path: "family-trees", component: FamilyTreeListView },
      { path: "family-trees/:treeId", component: FamilyTreeDetailView },
      { path: "family-trees/:treeId/collaborators", component: CollaboratorManageView },
      { path: "family-trees/:treeId/members", component: MemberListView },
      { path: "family-trees/:treeId/members/:memberId", component: MemberDetailView },
      { path: "family-trees/:treeId/query/ancestors", component: AncestorQueryView },
      { path: "family-trees/:treeId/query/kinship", component: KinshipQueryView }
    ]
  }
];

export default createRouter({
  history: createWebHistory(),
  routes
});

