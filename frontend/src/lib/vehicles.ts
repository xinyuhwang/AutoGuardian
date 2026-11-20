export type Vehicle = {
  id: number;
  vin: string | null;
  year: number;
  make: string;
  model: string;
  trim: string | null;
  engine: string | null;
  transmission: string | null;
  nickname: string | null;
  purchase_date: string | null;
  purchase_mileage: number | null;
  home_zip: string | null;
};

export type VehicleInput = Omit<Vehicle, "id">;

/** What NHTSA's VIN lookup proposes; nothing is saved until the user confirms. */
export type VinDecode = {
  vin: string;
  year: number | null;
  make: string | null;
  model: string | null;
  trim: string | null;
  engine: string | null;
  transmission: string | null;
  body_class: string | null;
  drive_type: string | null;
  fuel_type: string | null;
  warnings: string[];
  source: string;
};

export function vehicleTitle(v: Pick<Vehicle, "year" | "make" | "model">): string {
  return `${v.year} ${v.make} ${v.model}`;
}
