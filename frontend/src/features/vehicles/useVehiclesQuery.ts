import { useQuery } from "@tanstack/react-query";

import { fetchVehicles } from "./api";

export function useVehiclesQuery() {
  return useQuery({
    queryKey: ["vehicles", "mine"],
    queryFn: fetchVehicles,
  });
}
