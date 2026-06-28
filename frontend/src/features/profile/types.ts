export type ProfileData = {
  user_id: number;
  display_name: string;
  photo_url: string | null;
  country_code: string;
  phone_prefix: string;
  phone_number: string;
  phone_e164: string;
};

export type UpdateProfilePayload = {
  display_name?: string;
  photo_url?: string;
  country_code?: string;
  phone_prefix?: string;
  phone_number?: string;
};
