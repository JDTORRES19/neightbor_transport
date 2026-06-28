export type VehicleData = {
  id: number;
  brand: string;
  reference: string;
  color: string;
  plate: string;
  is_active: boolean;
};

export type ListVehiclesData = {
  items: VehicleData[];
};

export type CreateVehiclePayload = {
  brand: string;
  reference: string;
  color: string;
  plate: string;
};

export type UpdateVehiclePayload = {
  brand?: string;
  reference?: string;
  color?: string;
  plate?: string;
};
