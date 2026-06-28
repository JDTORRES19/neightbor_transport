import { useQuery } from "@tanstack/react-query";

import { fetchMyProfile } from "./api";

export function useProfileQuery() {
  return useQuery({
    queryKey: ["profile", "me"],
    queryFn: fetchMyProfile,
  });
}
