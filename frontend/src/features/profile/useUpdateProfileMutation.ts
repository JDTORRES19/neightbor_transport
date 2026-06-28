import { useMutation, useQueryClient } from "@tanstack/react-query";

import { updateMyProfile } from "./api";
import { UpdateProfilePayload } from "./types";

export function useUpdateProfileMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: UpdateProfilePayload) => updateMyProfile(payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["profile", "me"] });
    },
  });
}
