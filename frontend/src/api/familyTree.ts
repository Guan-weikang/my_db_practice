import client from "./client";

export function fetchFamilyTrees() {
  return client.get("/family-trees");
}

