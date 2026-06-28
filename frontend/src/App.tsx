import { FormEvent, useEffect, useState } from "react";

import { useProfileQuery } from "./features/profile/useProfileQuery";
import { useUpdateProfileMutation } from "./features/profile/useUpdateProfileMutation";
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
import { API_BASE_URL } from "./shared/api/config";
import { ApiRequestError } from "./shared/api/types";

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
  const tripsBoardQuery = useTripsBoardQuery();
  const myActiveTripQuery = useMyActiveTripQuery();

  const [displayName, setDisplayName] = useState("Usuario Demo");
  const [phonePrefix, setPhonePrefix] = useState("+57");
  const [phoneNumber, setPhoneNumber] = useState("");

  const [vehicleBrand, setVehicleBrand] = useState("");
  const [vehicleReference, setVehicleReference] = useState("");
  const [vehicleColor, setVehicleColor] = useState("");
  const [vehiclePlate, setVehiclePlate] = useState("");
  const [tripDirection, setTripDirection] = useState("to_cali");
  const [tripOriginLabel, setTripOriginLabel] = useState("Unidad La Arboleda");
  const [tripDepartureAt, setTripDepartureAt] = useState("");
  const [tripTotalSeats, setTripTotalSeats] = useState(4);
  const [actionFeedback, setActionFeedback] = useState<string>("");

  useEffect(() => {
    if (!profileQuery.data) {
      return;
    }

    setDisplayName(profileQuery.data.data.display_name);
    setPhonePrefix(profileQuery.data.data.phone_prefix);
    setPhoneNumber(profileQuery.data.data.phone_number);
  }, [profileQuery.data]);

  const healthStatus = isLoading ? "loading" : isError ? "error" : "ok";
  const requestId = data?.requestId ?? (error instanceof ApiRequestError ? error.requestId : "-") ?? "-";

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

        <div className="status-panel secondary-panel">
          <p className="section-title">Bootstrap Fase 1</p>
          <p>
            Perfil: {profileQuery.data?.data.display_name ?? (profileQuery.isLoading ? "cargando..." : "sin datos")}
          </p>
          <p>Vehiculos registrados: {vehiclesQuery.data?.data.items.length ?? 0}</p>
          <p>Viajes activos en board: {tripsBoardQuery.data?.data.items.length ?? 0}</p>

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
              <select value={tripDirection} onChange={(event) => setTripDirection(event.target.value)}>
                <option value="to_cali">Hacia Cali</option>
                <option value="to_jamundi">Hacia Jamundi</option>
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

          {actionFeedback && <p className="request-id">{actionFeedback}</p>}
        </div>
      </section>
    </main>
  );
}

export default App;
