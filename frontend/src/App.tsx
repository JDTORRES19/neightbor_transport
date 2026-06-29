import { FormEvent, useEffect, useRef, useState } from "react";

import { useProfileQuery } from "./features/profile/useProfileQuery";
import { useUpdateProfileMutation } from "./features/profile/useUpdateProfileMutation";
import {
  useAcceptTripRequestMutation,
  useCancelTripRequestMutation,
  useCreateTripRequestMutation,
  useRejectTripRequestMutation,
} from "./features/requests/useRequestMutations";
import { useMyRequestsQuery, useTripRequestsQuery } from "./features/requests/useRequestQueries";
import {
  useMarkAllNotificationsReadMutation,
  useUnreadNotificationsQuery,
} from "./features/notifications/useNotifications";
import { useMetricsOverviewQuery } from "./features/metrics/useMetricsOverviewQuery";
import { useHealthQuery } from "./features/system/health/useHealthQuery";
import {
  useCreateVehicleMutation,
  useDeactivateVehicleMutation,
} from "./features/vehicles/useVehicleMutations";
import { useVehiclesQuery } from "./features/vehicles/useVehiclesQuery";
import {
  useCancelTripMutation,
  useCreateTripMutation,
  useFinalizeTripMutation,
} from "./features/trips/useTripMutations";
import { useMyActiveTripQuery, useTripsBoardQuery } from "./features/trips/useTripsQueries";
import {
  BOARD_DIRECTION_OPTIONS,
  CANCELLABLE_REQUEST_STATUSES,
  REQUEST_STATUS,
  TRIP_DIRECTION_OPTIONS,
  type BoardDirectionValue,
  type TripDirectionValue,
  TRIP_STATUS,
} from "./shared/constants/trips";
import { API_BASE_URL } from "./shared/api/config";
import { ApiRequestError } from "./shared/api/types";
import { NotificationData } from "./features/notifications/types";

function App() {
  const { data, error, isLoading, isError, refetch } = useHealthQuery();
  const profileQuery = useProfileQuery();
  const vehiclesQuery = useVehiclesQuery();
  const updateProfileMutation = useUpdateProfileMutation();
  const createVehicleMutation = useCreateVehicleMutation();
  const deactivateVehicleMutation = useDeactivateVehicleMutation();
  const createTripMutation = useCreateTripMutation();
  const cancelTripMutation = useCancelTripMutation();
  const finalizeTripMutation = useFinalizeTripMutation();
  const createTripRequestMutation = useCreateTripRequestMutation();
  const acceptTripRequestMutation = useAcceptTripRequestMutation();
  const rejectTripRequestMutation = useRejectTripRequestMutation();
  const cancelTripRequestMutation = useCancelTripRequestMutation();
  const [boardDirection, setBoardDirection] = useState<BoardDirectionValue>("all");
  const tripsBoardQuery = useTripsBoardQuery(boardDirection === "all" ? undefined : boardDirection);
  const myActiveTripQuery = useMyActiveTripQuery();
  const tripRequestsQuery = useTripRequestsQuery(myActiveTripQuery.data?.data?.id);
  const myRequestsQuery = useMyRequestsQuery();
  const unreadNotificationsQuery = useUnreadNotificationsQuery();
  const markAllNotificationsReadMutation = useMarkAllNotificationsReadMutation();
  const [latencyWindowSeconds, setLatencyWindowSeconds] = useState(300);
  const metricsOverviewQuery = useMetricsOverviewQuery({ windowSeconds: latencyWindowSeconds, limit: 12 });

  const [displayName, setDisplayName] = useState("Usuario Demo");
  const [phonePrefix, setPhonePrefix] = useState("+57");
  const [phoneNumber, setPhoneNumber] = useState("");

  const [vehicleBrand, setVehicleBrand] = useState("");
  const [vehicleReference, setVehicleReference] = useState("");
  const [vehicleColor, setVehicleColor] = useState("");
  const [vehiclePlate, setVehiclePlate] = useState("");
  const [tripDirection, setTripDirection] = useState<TripDirectionValue>(TRIP_DIRECTION_OPTIONS[0].value);
  const [tripOriginLabel, setTripOriginLabel] = useState("Unidad La Arboleda");
  const [tripDepartureAt, setTripDepartureAt] = useState("");
  const [tripTotalSeats, setTripTotalSeats] = useState(4);
  const [selectedBoardTripId, setSelectedBoardTripId] = useState<number | null>(null);
  const [requestPickupLabel, setRequestPickupLabel] = useState("Porteria principal");
  const [requestRequestedSeats, setRequestRequestedSeats] = useState(1);
  const [requestComment, setRequestComment] = useState("Voy con maleta");
  const [autoCancelledByAcceptIds, setAutoCancelledByAcceptIds] = useState<number[]>([]);
  const [actionFeedback, setActionFeedback] = useState<string>("");
  const [toastNotifications, setToastNotifications] = useState<NotificationData[]>([]);
  const seenToastIdsRef = useRef<Set<number>>(new Set());

  useEffect(() => {
    if (!profileQuery.data) {
      return;
    }

    setDisplayName(profileQuery.data.data.display_name);
    setPhonePrefix(profileQuery.data.data.phone_prefix);
    setPhoneNumber(profileQuery.data.data.phone_number);
  }, [profileQuery.data]);

  useEffect(() => {
    const unreadItems = unreadNotificationsQuery.data?.data.items ?? [];
    if (unreadItems.length === 0) {
      return;
    }

    const newItems = unreadItems.filter((item) => !seenToastIdsRef.current.has(item.id));
    if (newItems.length === 0) {
      return;
    }

    newItems.forEach((item) => seenToastIdsRef.current.add(item.id));
    setToastNotifications((current) => [...newItems, ...current].slice(0, 6));

    void markAllNotificationsReadMutation.mutateAsync().catch(() => {
      // Keep unread state if the mark-as-read call fails.
    });
  }, [unreadNotificationsQuery.dataUpdatedAt]);

  const healthStatus = isLoading ? "loading" : isError ? "error" : "ok";
  const requestId = data?.requestId ?? (error instanceof ApiRequestError ? error.requestId : "-") ?? "-";
  const tripRequests = tripRequestsQuery.data?.data.items ?? [];
  const myRequests = myRequestsQuery.data?.data.items ?? [];
  const boardTrips = tripsBoardQuery.data?.data.items ?? [];

  let healthMessage = "Validando conexion con la API...";
  if (!isLoading && data) {
    healthMessage = `API ${data.data.service}: ${data.data.status}`;
  }
  if (isError) {
    if (error instanceof ApiRequestError) {
      healthMessage = `${error.code}: ${error.message}`;
    } else {
      healthMessage = "No fue posible conectar con la API.";
    }
  }

  const handleProfileSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setActionFeedback("");

    try {
      await updateProfileMutation.mutateAsync({
        display_name: displayName,
        phone_prefix: phonePrefix,
        phone_number: phoneNumber,
      });
      setActionFeedback("Perfil actualizado correctamente.");
    } catch (mutationError) {
      if (mutationError instanceof ApiRequestError) {
        setActionFeedback(`${mutationError.code}: ${mutationError.message}`);
        return;
      }
      setActionFeedback("No fue posible actualizar el perfil.");
    }
  };

  const handleCreateVehicle = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setActionFeedback("");

    try {
      await createVehicleMutation.mutateAsync({
        brand: vehicleBrand,
        reference: vehicleReference,
        color: vehicleColor,
        plate: vehiclePlate,
      });

      setVehicleBrand("");
      setVehicleReference("");
      setVehicleColor("");
      setVehiclePlate("");
      setActionFeedback("Vehiculo creado correctamente.");
    } catch (mutationError) {
      if (mutationError instanceof ApiRequestError) {
        setActionFeedback(`${mutationError.code}: ${mutationError.message}`);
        return;
      }
      setActionFeedback("No fue posible crear el vehiculo.");
    }
  };

  const handleDeactivateVehicle = async (vehicleId: number) => {
    setActionFeedback("");

    try {
      await deactivateVehicleMutation.mutateAsync(vehicleId);
      setActionFeedback("Vehiculo desactivado.");
    } catch (mutationError) {
      if (mutationError instanceof ApiRequestError) {
        setActionFeedback(`${mutationError.code}: ${mutationError.message}`);
        return;
      }
      setActionFeedback("No fue posible desactivar el vehiculo.");
    }
  };

  const handleCreateTrip = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setActionFeedback("");

    const activeVehicle = (vehiclesQuery.data?.data.items ?? []).find((item) => item.is_active);
    if (!activeVehicle) {
      setActionFeedback("Necesitas al menos un vehiculo activo para publicar viaje.");
      return;
    }

    if (!tripDepartureAt) {
      setActionFeedback("Debes definir la fecha y hora de salida.");
      return;
    }

    try {
      await createTripMutation.mutateAsync({
        direction: tripDirection,
        origin_label: tripOriginLabel,
        departure_at: new Date(tripDepartureAt).toISOString(),
        total_seats: tripTotalSeats,
        vehicle_id: activeVehicle.id,
      });
      setActionFeedback("Viaje publicado correctamente.");
    } catch (mutationError) {
      if (mutationError instanceof ApiRequestError) {
        setActionFeedback(`${mutationError.code}: ${mutationError.message}`);
        return;
      }
      setActionFeedback("No fue posible crear el viaje.");
    }
  };

  const myActiveTrip = myActiveTripQuery.data?.data;

  const handleCancelTrip = async () => {
    if (!myActiveTrip) {
      return;
    }
    setActionFeedback("");
    try {
      await cancelTripMutation.mutateAsync(myActiveTrip.id);
      setActionFeedback("Viaje cancelado.");
    } catch (mutationError) {
      if (mutationError instanceof ApiRequestError) {
        setActionFeedback(`${mutationError.code}: ${mutationError.message}`);
        return;
      }
      setActionFeedback("No fue posible cancelar el viaje.");
    }
  };

  const handleFinalizeTrip = async () => {
    if (!myActiveTrip) {
      return;
    }
    setActionFeedback("");
    try {
      await finalizeTripMutation.mutateAsync(myActiveTrip.id);
      setActionFeedback("Viaje finalizado.");
    } catch (mutationError) {
      if (mutationError instanceof ApiRequestError) {
        setActionFeedback(`${mutationError.code}: ${mutationError.message}`);
        return;
      }
      setActionFeedback("No fue posible finalizar el viaje.");
    }
  };

  const handleCreateRequestOnBoardTrip = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (!selectedBoardTripId) {
      setActionFeedback("Selecciona un viaje del board para solicitar cupos.");
      return;
    }

    setActionFeedback("");

    try {
      await createTripRequestMutation.mutateAsync({
        tripId: selectedBoardTripId,
        payload: {
          pickup_label: requestPickupLabel,
          requested_seats: requestRequestedSeats,
          comment: requestComment,
        },
      });
      setActionFeedback("Solicitud creada correctamente.");
      setSelectedBoardTripId(null);
    } catch (mutationError) {
      if (mutationError instanceof ApiRequestError) {
        setActionFeedback(`${mutationError.code}: ${mutationError.message}`);
        return;
      }
      setActionFeedback("No fue posible crear la solicitud.");
    }
  };

  const handleSelectTripForRequest = (tripId: number) => {
    setSelectedBoardTripId((current) => (current === tripId ? null : tripId));
    setActionFeedback("");
  };

  const handleBoardDirectionChange = (value: string) => {
    const selectedOption = BOARD_DIRECTION_OPTIONS.find((option) => option.value === value);
    if (selectedOption) {
      setBoardDirection(selectedOption.value);
      setSelectedBoardTripId(null);
    }
  };

  const handleTripDirectionChange = (value: string) => {
    const selectedOption = TRIP_DIRECTION_OPTIONS.find((option) => option.value === value);
    if (selectedOption) {
      setTripDirection(selectedOption.value);
    }
  };

  const handleAcceptRequest = async (requestId: number) => {
    setActionFeedback("");

    const acceptedRequest = tripRequests.find((item) => item.id === requestId);
    const requesterUserId = acceptedRequest?.requester.user_id;
    const autoCancelledIds =
      requesterUserId === undefined
        ? []
        : myRequests
            .filter(
              (item) =>
                item.id !== requestId &&
                item.requester.user_id === requesterUserId &&
                item.status === REQUEST_STATUS.PENDING,
            )
            .map((item) => item.id);

    try {
      await acceptTripRequestMutation.mutateAsync(requestId);
      if (autoCancelledIds.length > 0) {
        setAutoCancelledByAcceptIds((current) =>
          Array.from(new Set([...current, ...autoCancelledIds])),
        );
        setActionFeedback(
          `Solicitud aceptada. ${autoCancelledIds.length} solicitud(es) pendiente(s) del mismo solicitante se cancelaron automaticamente.`,
        );
      } else {
        setActionFeedback("Solicitud aceptada.");
      }
    } catch (mutationError) {
      if (mutationError instanceof ApiRequestError) {
        setActionFeedback(`${mutationError.code}: ${mutationError.message}`);
        return;
      }
      setActionFeedback("No fue posible aceptar la solicitud.");
    }
  };

  const handleRejectRequest = async (requestId: number) => {
    setActionFeedback("");
    try {
      await rejectTripRequestMutation.mutateAsync(requestId);
      setActionFeedback("Solicitud rechazada.");
    } catch (mutationError) {
      if (mutationError instanceof ApiRequestError) {
        setActionFeedback(`${mutationError.code}: ${mutationError.message}`);
        return;
      }
      setActionFeedback("No fue posible rechazar la solicitud.");
    }
  };

  const handleCancelOwnRequest = async (requestId: number) => {
    setActionFeedback("");
    try {
      await cancelTripRequestMutation.mutateAsync(requestId);
      setAutoCancelledByAcceptIds((current) => current.filter((item) => item !== requestId));
      setActionFeedback("Solicitud cancelada.");
    } catch (mutationError) {
      if (mutationError instanceof ApiRequestError) {
        setActionFeedback(`${mutationError.code}: ${mutationError.message}`);
        return;
      }
      setActionFeedback("No fue posible cancelar la solicitud.");
    }
  };

  const handleDismissToast = (notificationId: number) => {
    setToastNotifications((current) => current.filter((item) => item.id !== notificationId));
  };

  return (
    <main className="app-shell">
      <section className="card">
        <p className="eyebrow">Transporte Vecinal</p>
        <h1>Frontend Fase 0 activo</h1>
        <p>
          Stack confirmado: React + TypeScript + Vite. API objetivo: <code>{API_BASE_URL}</code>
        </p>

        <div className="status-panel">
          <span className={`status-badge status-${healthStatus}`}>
            {healthStatus === "loading" && "Verificando"}
            {healthStatus === "ok" && "Conectado"}
            {healthStatus === "error" && "Con error"}
          </span>
          <p>{healthMessage}</p>
          <p className="request-id">request_id: {requestId}</p>
          <button type="button" onClick={() => void refetch()}>
            Reintentar health check
          </button>
        </div>

        {toastNotifications.length > 0 && (
          <div className="toast-stack" aria-live="polite">
            {toastNotifications.map((item) => (
              <article key={item.id} className="toast-card">
                <div>
                  <p className="section-title">{item.title}</p>
                  <p>{item.body}</p>
                  <p className="request-id">{new Date(item.created_at).toLocaleString()}</p>
                </div>
                <button type="button" onClick={() => handleDismissToast(item.id)}>
                  Cerrar
                </button>
              </article>
            ))}
          </div>
        )}

        <div className="status-panel secondary-panel">
          <p className="section-title">Bootstrap Fase 1</p>
          <p>
            Perfil: {profileQuery.data?.data.display_name ?? (profileQuery.isLoading ? "cargando..." : "sin datos")}
          </p>
          <p>Notificaciones no leidas: {unreadNotificationsQuery.data?.data.unread_count ?? 0}</p>
          <p>Vehiculos registrados: {vehiclesQuery.data?.data.items.length ?? 0}</p>
          <p>Viajes activos en board: {tripsBoardQuery.data?.data.items.length ?? 0}</p>

          <div className="metrics-panel">
            <p className="section-title">Observabilidad Fase 6</p>
            <label className="latency-controls">
              Ventana latencia
              <select
                value={latencyWindowSeconds}
                onChange={(event) => setLatencyWindowSeconds(Number(event.target.value))}
              >
                <option value={60}>1 min</option>
                <option value={300}>5 min</option>
                <option value={900}>15 min</option>
              </select>
            </label>
            <p>Viajes por estado: {JSON.stringify(metricsOverviewQuery.data?.data.trips_by_status ?? {})}</p>
            <p>
              Solicitudes por estado: {JSON.stringify(metricsOverviewQuery.data?.data.requests_by_status ?? {})}
            </p>
            <p>Notificaciones totales: {metricsOverviewQuery.data?.data.total_notifications ?? 0}</p>
            <p>Notificaciones no leidas: {metricsOverviewQuery.data?.data.unread_notifications ?? 0}</p>
            <p>Eventos de auditoria: {metricsOverviewQuery.data?.data.total_audit_events ?? 0}</p>
            <p>
              Ultimo scheduler: {metricsOverviewQuery.data?.data.last_scheduler_run?.status ?? "sin ejecuciones"}
              {metricsOverviewQuery.data?.data.last_scheduler_run
                ? ` (${metricsOverviewQuery.data.data.last_scheduler_run.processed_count} procesados)`
                : ""}
            </p>
            <p>Ventana activa: {metricsOverviewQuery.data?.data.latency_window_seconds ?? latencyWindowSeconds}s</p>
            <div>
              <p className="section-title">Latencia por endpoint (ms)</p>
              <ul className="latency-list">
                {(metricsOverviewQuery.data?.data.endpoint_latency_ms ?? []).map((item) => (
                  <li key={`${item.method}-${item.path}-${item.status_code}`}>
                    {item.method} {item.path} [{item.status_code}] - avg {item.avg_ms}, p95 {item.p95_ms}, max {item.max_ms} ({item.count} req)
                  </li>
                ))}
                {(metricsOverviewQuery.data?.data.endpoint_latency_ms ?? []).length === 0 && (
                  <li>Sin datos de latencia aun.</li>
                )}
              </ul>
            </div>
          </div>

          <form className="form-grid" onSubmit={handleProfileSubmit}>
            <label>
              Nombre visible
              <input value={displayName} onChange={(event) => setDisplayName(event.target.value)} />
            </label>
            <label>
              Prefijo
              <input value={phonePrefix} onChange={(event) => setPhonePrefix(event.target.value)} />
            </label>
            <label>
              Telefono
              <input value={phoneNumber} onChange={(event) => setPhoneNumber(event.target.value)} />
            </label>
            <button type="submit" disabled={updateProfileMutation.isPending}>
              Guardar perfil
            </button>
          </form>

          <form className="form-grid" onSubmit={handleCreateVehicle}>
            <label>
              Marca
              <input value={vehicleBrand} onChange={(event) => setVehicleBrand(event.target.value)} required />
            </label>
            <label>
              Referencia
              <input
                value={vehicleReference}
                onChange={(event) => setVehicleReference(event.target.value)}
                required
              />
            </label>
            <label>
              Color
              <input value={vehicleColor} onChange={(event) => setVehicleColor(event.target.value)} required />
            </label>
            <label>
              Placa
              <input value={vehiclePlate} onChange={(event) => setVehiclePlate(event.target.value)} required />
            </label>
            <button type="submit" disabled={createVehicleMutation.isPending}>
              Crear vehiculo
            </button>
          </form>

          <ul className="vehicle-list">
            {(vehiclesQuery.data?.data.items ?? []).map((vehicle) => (
              <li key={vehicle.id}>
                <span>
                  {vehicle.brand} {vehicle.reference} - {vehicle.plate} ({vehicle.is_active ? "activo" : "inactivo"})
                </span>
                <button
                  type="button"
                  disabled={!vehicle.is_active || deactivateVehicleMutation.isPending}
                  onClick={() => void handleDeactivateVehicle(vehicle.id)}
                >
                  Desactivar
                </button>
              </li>
            ))}
          </ul>

          <form className="form-grid" onSubmit={handleCreateTrip}>
            <label>
              Direccion
              <select value={tripDirection} onChange={(event) => handleTripDirectionChange(event.target.value)}>
                {TRIP_DIRECTION_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Origen
              <input value={tripOriginLabel} onChange={(event) => setTripOriginLabel(event.target.value)} required />
            </label>
            <label>
              Salida
              <input
                type="datetime-local"
                value={tripDepartureAt}
                onChange={(event) => setTripDepartureAt(event.target.value)}
                required
              />
            </label>
            <label>
              Cupos
              <input
                type="number"
                min={1}
                max={12}
                value={tripTotalSeats}
                onChange={(event) => setTripTotalSeats(Number(event.target.value))}
                required
              />
            </label>
            <button type="submit" disabled={createTripMutation.isPending}>
              Publicar viaje
            </button>
          </form>

          <div className="trip-actions">
            <p>
              Mi viaje activo: {myActiveTrip ? `#${myActiveTrip.id} (${myActiveTrip.status})` : "ninguno"}
            </p>
            <div className="inline-actions">
              <button
                type="button"
                disabled={!myActiveTrip || cancelTripMutation.isPending}
                onClick={() => void handleCancelTrip()}
              >
                Cancelar viaje
              </button>
              <button
                type="button"
                disabled={!myActiveTrip || finalizeTripMutation.isPending}
                onClick={() => void handleFinalizeTrip()}
              >
                Finalizar viaje
              </button>
            </div>
          </div>

          <div className="requests-panel">
            <p className="section-title">Board de viajes (lado solicitante)</p>
            <label className="board-filter">
              Trayecto
              <select value={boardDirection} onChange={(event) => handleBoardDirectionChange(event.target.value)}>
                {BOARD_DIRECTION_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>
            <ul className="request-list">
              {boardTrips.length === 0 && <li>No hay viajes activos en el board.</li>}
              {boardTrips.map((trip) => {
                const isOwnTrip = trip.driver.user_id === profileQuery.data?.data.user_id;
                const isNotAvailable = trip.status !== TRIP_STATUS.ACTIVE || trip.available_seats <= 0;
                const isDisabled = isOwnTrip || isNotAvailable;
                return (
                  <li key={trip.id}>
                    <div>
                      <strong>
                        Viaje #{trip.id} - {trip.driver.display_name}
                      </strong>
                      <p>
                        {trip.origin_label} | salida {new Date(trip.departure_at).toLocaleString()} | estado {trip.status}
                      </p>
                      <p>
                        Cupos disponibles: {trip.available_seats} / {trip.total_seats}
                      </p>
                      {isOwnTrip && <p className="request-id">No puedes solicitar cupos en tu propio viaje.</p>}
                      {!isOwnTrip && isNotAvailable && <p className="request-id">Este viaje no acepta nuevas solicitudes.</p>}
                    </div>

                    <div className="inline-actions">
                      <button
                        type="button"
                        disabled={isDisabled}
                        onClick={() => handleSelectTripForRequest(trip.id)}
                      >
                        {selectedBoardTripId === trip.id ? "Ocultar formulario" : "Solicitar cupo"}
                      </button>
                    </div>
                  </li>
                );
              })}
            </ul>

            {selectedBoardTripId && (
              <form className="form-grid" onSubmit={handleCreateRequestOnBoardTrip}>
                <p className="section-title">Crear solicitud para viaje #{selectedBoardTripId}</p>
                <label>
                  Punto de recogida
                  <input
                    value={requestPickupLabel}
                    onChange={(event) => setRequestPickupLabel(event.target.value)}
                    required
                  />
                </label>
                <label>
                  Cupos solicitados
                  <input
                    type="number"
                    min={1}
                    max={12}
                    value={requestRequestedSeats}
                    onChange={(event) => setRequestRequestedSeats(Number(event.target.value))}
                    required
                  />
                </label>
                <label>
                  Comentario
                  <input value={requestComment} onChange={(event) => setRequestComment(event.target.value)} />
                </label>
                <button type="submit" disabled={createTripRequestMutation.isPending}>
                  Crear solicitud
                </button>
              </form>
            )}
          </div>

          <div className="requests-panel">
            <p className="section-title">Solicitudes de mi viaje activo</p>
            {!myActiveTrip && <p className="request-id">Activa un viaje para gestionar solicitudes.</p>}

            {myActiveTrip && (
              <ul className="request-list">
                {tripRequests.length === 0 && <li>No hay solicitudes registradas.</li>}
                {tripRequests.map((item) => (
                  <li key={item.id}>
                    <div>
                      <strong>{item.requester.display_name}</strong>
                      <p>
                        {item.requested_seats} cupo(s) - {item.pickup_label} - estado: {item.status}
                      </p>
                      {item.comment && <p>Comentario: {item.comment}</p>}
                    </div>

                    <div className="inline-actions">
                      <button
                        type="button"
                        disabled={item.status !== REQUEST_STATUS.PENDING || acceptTripRequestMutation.isPending}
                        onClick={() => void handleAcceptRequest(item.id)}
                      >
                        Aceptar
                      </button>
                      <button
                        type="button"
                        disabled={item.status !== REQUEST_STATUS.PENDING || rejectTripRequestMutation.isPending}
                        onClick={() => void handleRejectRequest(item.id)}
                      >
                        Rechazar
                      </button>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div>

          <div className="requests-panel">
            <p className="section-title">Mis solicitudes (simulacion solicitante)</p>
            <ul className="request-list">
              {myRequests.length === 0 && <li>No hay solicitudes creadas.</li>}
              {myRequests.map((item) => (
                <li key={item.id}>
                  <div>
                    <strong>Viaje #{item.trip_id}</strong>
                    <p>
                      {item.requested_seats} cupo(s) - {item.pickup_label} - estado: {item.status}
                    </p>
                    {item.status === REQUEST_STATUS.CANCELLED && autoCancelledByAcceptIds.includes(item.id) && (
                      <p className="auto-cancel-note">
                        Cancelada automaticamente al aceptar otra solicitud del mismo solicitante
                        {item.decided_at ? ` (${new Date(item.decided_at).toLocaleString()})` : ""}.
                      </p>
                    )}
                  </div>
                  <button
                    type="button"
                    disabled={
                      !CANCELLABLE_REQUEST_STATUSES.includes(
                        item.status as (typeof CANCELLABLE_REQUEST_STATUSES)[number],
                      ) || cancelTripRequestMutation.isPending
                    }
                    onClick={() => void handleCancelOwnRequest(item.id)}
                  >
                    Cancelar
                  </button>
                </li>
              ))}
            </ul>
          </div>

          {actionFeedback && <p className="request-id">{actionFeedback}</p>}
        </div>
      </section>
    </main>
  );
}

export default App;
