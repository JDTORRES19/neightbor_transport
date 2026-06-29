export const BOARD_DIRECTION_OPTIONS = [
  { value: "all", label: "Todos" },
  { value: "to_cali", label: "Hacia Cali" },
  { value: "to_jamundi", label: "Hacia Jamundi" },
] as const;

export type BoardDirectionValue = (typeof BOARD_DIRECTION_OPTIONS)[number]["value"];

export const TRIP_DIRECTION_OPTIONS = [
  { value: "to_cali", label: "Hacia Cali" },
  { value: "to_jamundi", label: "Hacia Jamundi" },
] as const;

export type TripDirectionValue = (typeof TRIP_DIRECTION_OPTIONS)[number]["value"];

export const REQUEST_STATUS = {
  PENDING: "pendiente",
  ACCEPTED: "aceptada",
  REJECTED: "rechazada",
  CANCELLED: "cancelada",
} as const;

export const TRIP_STATUS = {
  ACTIVE: "activo",
  FULL: "lleno",
  CANCELLED: "cancelado",
  FINALIZED: "finalizado",
} as const;

export const CANCELLABLE_REQUEST_STATUSES = [
  REQUEST_STATUS.PENDING,
  REQUEST_STATUS.ACCEPTED,
] as const;
