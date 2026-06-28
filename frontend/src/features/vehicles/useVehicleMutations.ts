import { useMutation, useQueryClient } from "@tanstack/react-query";

import { createVehicle, deactivateVehicle } from "./api";
import { CreateVehiclePayload } from "./types";

export function useCreateVehicleMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: CreateVehiclePayload) => createVehicle(payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["vehicles", "mine"] });
    },
  });
}

export function useDeactivateVehicleMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (vehicleId: number) => deactivateVehicle(vehicleId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["vehicles", "mine"] });
    },
  });
}
