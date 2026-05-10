import { ref } from "vue";

export function usePagination() {
  const page = ref(1);
  const pageSize = ref(20);
  return { page, pageSize };
}

