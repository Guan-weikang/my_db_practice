export function useFamilyTreePermission() {
  const canEdit = (role: string) => role === "creator" || role === "collaborator";
  const canRead = (role: string) => role === "creator" || role === "collaborator" || role === "reader";
  return { canEdit, canRead };
}

