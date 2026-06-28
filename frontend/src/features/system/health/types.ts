export type HealthData = {
  status: string;
  service: string;
};

export type HealthQueryResult = {
  data: HealthData;
  requestId?: string;
};
