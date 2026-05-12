import client from "./client";

export type DashboardSummary = {
  total_members: number;
  male_count: number;
  female_count: number;
  unknown_count: number;
  male_ratio: number | null;
  female_ratio: number | null;
};

export type DashboardResponse = {
  tree_id: number;
  summary: DashboardSummary;
};

export type GenerationMaxAverageLifespanItem = {
  generation_no: number;
  avg_lifespan_years: number;
};

export type GenerationMaxAverageLifespanResponse = {
  tree_id: number;
  item: GenerationMaxAverageLifespanItem | null;
};

export type OlderThan50UnmarriedMaleItem = {
  member_id: number;
  name: string;
  birth_date: string;
  age_years: number;
  generation_no: number | null;
  generation_name: string | null;
};

export type OlderThan50UnmarriedMaleResponse = {
  tree_id: number;
  items: OlderThan50UnmarriedMaleItem[];
};

export type BeforeGenerationAverageBirthYearItem = {
  member_id: number;
  name: string;
  generation_no: number;
  generation_name: string | null;
  birth_year: number;
  avg_birth_year: number;
};

export type BeforeGenerationAverageBirthYearResponse = {
  tree_id: number;
  items: BeforeGenerationAverageBirthYearItem[];
};

export function fetchDashboard(treeId: number) {
  return client.get<DashboardResponse>(`/family-trees/${treeId}/analytics/dashboard`);
}

export function fetchMaxAverageLifespan(treeId: number) {
  return client.get<GenerationMaxAverageLifespanResponse>(
    `/family-trees/${treeId}/analytics/generation/max-average-lifespan`
  );
}

export function fetchOlderThan50UnmarriedMale(treeId: number) {
  return client.get<OlderThan50UnmarriedMaleResponse>(
    `/family-trees/${treeId}/analytics/members/older-than-50-unmarried-male`
  );
}

export function fetchBeforeGenerationAverageBirthYear(treeId: number) {
  return client.get<BeforeGenerationAverageBirthYearResponse>(
    `/family-trees/${treeId}/analytics/members/before-generation-average-birth-year`
  );
}
