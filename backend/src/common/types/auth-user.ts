import { Role, UserStatus } from '@prisma/client';

export interface AuthUser {
  id: string;
  code: string;
  fullName: string;
  role: Role;
  status: UserStatus;
}

export interface JwtPayload {
  sub: string;
  code: string;
  role: Role;
  iat?: number;
  exp?: number;
}
