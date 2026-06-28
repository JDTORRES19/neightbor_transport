export type TripRequestRequesterData = {
  user_id: number;
  display_name: string;
  photo_url: string | null;
};

export type TripRequestData = {
  id: number;
  trip_id: number;
  pickup_label: string;
  requested_seats: number;
  comment: string | null;
  status: string;
  created_at: string;
  decided_at: string | null;
  requester: TripRequestRequesterData;
};

export type TripRequestsListData = {
  items: TripRequestData[];
};

export type CreateTripRequestPayload = {
  pickup_label: string;
  requested_seats: number;
  comment?: string;
};
