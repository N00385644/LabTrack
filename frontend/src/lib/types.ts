export type Role = 'STUDENT' | 'ADMIN';
export type UserStatus = 'ACTIVE' | 'PENALIZED';
export type EquipmentStatus = 'AVAILABLE' | 'BORROWED';
export type ReservationStatus = 'PENDING' | 'APPROVED' | 'REJECTED' | 'RETURNED';

export interface User {
  id: string;
  code: string;
  fullName: string;
  email: string;
  role: Role;
  status: UserStatus;
}

export interface Equipment {
  id: string;
  name: string;
  inventoryCode: string;
  category: string;
  status: EquipmentStatus;
  description: string;
  location: string;
}

export interface ReservationStudent {
  id: string;
  code: string;
  fullName: string;
  status: UserStatus;
}

export interface ReservationEquipment {
  id: string;
  name: string;
  inventoryCode: string;
  category: string;
  status: EquipmentStatus;
  location: string;
}

export interface Reservation {
  id: string;
  date: string;
  startTime: string;
  endTime: string;
  status: ReservationStatus;
  rejectionReason: string | null;
  penaltyApplied: boolean;
  reviewedBy: string | null;
  reviewedAt: string | null;
  returnedAt: string | null;
  createdAt: string;
  student: ReservationStudent;
  equipment: ReservationEquipment;
}

export interface LoginResponse {
  accessToken: string;
  expiresIn: string;
  user: User;
}

export interface CatalogStats {
  total: number;
  available: number;
  borrowed: number;
  pending: number;
  students: number;
}

export interface AdminStats {
  pending: number;
  approved: number;
  returnsToday: number;
  penalized: number;
  equipmentTotal: number;
  equipmentAvailable: number;
}

export interface AuditEvent {
  id: string;
  event: string;
  actorCode: string;
  detail: string;
  ipAddress: string;
  createdAt: string;
}
