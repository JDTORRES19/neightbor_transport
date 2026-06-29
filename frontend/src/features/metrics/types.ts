export type SchedulerJobRunData = {
  id: number;
  job_name: string;
  status: string;
  processed_count: number;
  started_at: string;
  finished_at: string | null;
};

export type EndpointLatencyData = {
  method: string;
  path: string;
  status_code: number;
  count: number;
  avg_ms: number;
  p95_ms: number;
  max_ms: number;
};

export type MetricsOverviewData = {
  trips_by_status: Record<string, number>;
  requests_by_status: Record<string, number>;
  total_notifications: number;
  unread_notifications: number;
  total_audit_events: number;
  last_scheduler_run: SchedulerJobRunData | null;
  latency_window_seconds: number;
  endpoint_latency_ms: EndpointLatencyData[];
};
