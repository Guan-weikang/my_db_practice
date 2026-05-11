export function useFamilyTreePermission() {
  const canEdit = (role: string) => role === "creator" || role === "collaborator";
  const canRead = (role: string) => role === "creator" || role === "collaborator" || role === "reader";
  const canManageCollaborators = (role: string) => role === "creator";
  return { canEdit, canRead, canManageCollaborators };
}
