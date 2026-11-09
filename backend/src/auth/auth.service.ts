import { Injectable, UnauthorizedException } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { JwtService } from '@nestjs/jwt';
import { User } from '@prisma/client';
import * as bcrypt from 'bcryptjs';
import { DomainException } from '../common/exceptions/domain.exception';
import { JwtPayload } from '../common/types/auth-user';
import { PrismaService } from '../prisma/prisma.service';
import { AuditService } from '../audit/audit.service';
import { LoginDto } from './dto/login.dto';

const MAX_FAILED_ATTEMPTS = 3;
const LOCKOUT_MINUTES = 5;
const DUMMY_HASH = bcrypt.hashSync('labtrack-dummy-password-not-used', 10);

export interface SafeUser {
  id: string;
  code: string;
  fullName: string;
  email: string;
  role: string;
  status: string;
}

export interface LoginResult {
  accessToken: string;
  expiresIn: string;
  user: SafeUser;
}

@Injectable()
export class AuthService {
  constructor(
    private readonly prisma: PrismaService,
    private readonly jwt: JwtService,
    private readonly audit: AuditService,
    private readonly config: ConfigService,
  ) {}

  private toSafeUser(user: User): SafeUser {
    return {
      id: user.id,
      code: user.code,
      fullName: user.fullName,
      email: user.email,
      role: user.role,
      status: user.status,
    };
  }

  async login(dto: LoginDto, ipAddress = ''): Promise<LoginResult> {
    const normalizedCode = dto.code.trim().toUpperCase();
    const user = await this.prisma.user.findFirst({
      where: { code: { equals: normalizedCode, mode: 'insensitive' } },
    });
    const now = new Date();

    if (!user) {
      await bcrypt.compare(dto.password, DUMMY_HASH);
      await this.audit.record('LOGIN_FAILED', {
        actorCode: normalizedCode,
        detail: 'Usuario inexistente',
        ipAddress,
      });
      throw new UnauthorizedException('Credenciales inválidas.');
    }

    if (user.lockedUntil && user.lockedUntil > now) {
      const minutes = Math.max(
        1,
        Math.ceil((user.lockedUntil.getTime() - now.getTime()) / 60_000),
      );
      await this.audit.record('LOGIN_BLOCKED', {
        actorCode: user.code,
        detail: 'Intento en cuenta bloqueada',
        ipAddress,
        userId: user.id,
      });
      throw new DomainException(
        `Cuenta bloqueada temporalmente por seguridad. Intenta nuevamente en ${minutes} minuto(s).`,
        423,
        'ACCOUNT_LOCKED',
      );
    }

    if (user.lockedUntil && user.lockedUntil <= now) {
      await this.prisma.user.update({
        where: { id: user.id },
        data: { failedAttempts: 0, lockedUntil: null },
      });
      user.failedAttempts = 0;
      user.lockedUntil = null;
    }

    const passwordMatches = await bcrypt.compare(dto.password, user.passwordHash);
    if (!passwordMatches) {
      const attempts = user.failedAttempts + 1;
      if (attempts >= MAX_FAILED_ATTEMPTS) {
        const lockedUntil = new Date(now.getTime() + LOCKOUT_MINUTES * 60_000);
        await this.prisma.user.update({
          where: { id: user.id },
          data: { failedAttempts: 0, lockedUntil },
        });
        await this.audit.record('LOGIN_LOCKED', {
          actorCode: user.code,
          detail: `Bloqueo automático por ${MAX_FAILED_ATTEMPTS} intentos fallidos`,
          ipAddress,
          userId: user.id,
        });
        throw new DomainException(
          `Cuenta bloqueada temporalmente por seguridad. Intenta nuevamente en ${LOCKOUT_MINUTES} minutos.`,
          423,
          'ACCOUNT_LOCKED',
        );
      }

      await this.prisma.user.update({
        where: { id: user.id },
        data: { failedAttempts: attempts },
      });
      await this.audit.record('LOGIN_FAILED', {
        actorCode: user.code,
        detail: 'Contraseña incorrecta',
        ipAddress,
        userId: user.id,
      });
      throw new UnauthorizedException('Credenciales inválidas.');
    }

    const updated = await this.prisma.user.update({
      where: { id: user.id },
      data: { failedAttempts: 0, lockedUntil: null },
    });
    await this.audit.record('LOGIN_SUCCESS', {
      actorCode: user.code,
      detail: 'Inicio de sesión exitoso',
      ipAddress,
      userId: user.id,
    });

    const payload: JwtPayload = { sub: user.id, code: user.code, role: user.role };
    const expiresIn = this.config.get<string>('JWT_EXPIRES_IN') ?? '8h';
    const accessToken = await this.jwt.signAsync(payload, {
      expiresIn: expiresIn as never,
    });

    return {
      accessToken,
      expiresIn,
      user: this.toSafeUser(updated),
    };
  }
}
