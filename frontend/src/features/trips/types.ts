export type TripDriverData = {
  user_id: number;
  display_name: string;
  photo_url: string | null;
};

export type TripVehicleData = {
  id: number;
  brand: string;
  reference: string;
  color: string;
  plate: string;
};

export type TripData = {
  id: number;
  direction: string;
  origin_label: string;
  departure_at: string;
  published_at: string;
  status: string;
  total_seats: number;
  available_seats: number;
  driver: TripDriverData;
  vehicle: TripVehicleData;
};

export type TripsListData = {
  items: TripData[];
};

export type TripMaybeData = TripData | null;

export type CreateTripPayload = {
  direction: string;
  origin_label: string;
  departure_at: string;
  total_seats: number;
  vehicle_id: number;
};
