import { Injectable } from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service';

export interface AuditEventInput {
  actorCode?: string;
  detail?: string;
  ipAddress?: string;
  userId?: string | null;
}

@Injectable()
export class AuditService {
  constructor(private readonly prisma: PrismaService) {}

  async record(event: string, input: AuditEventInput = {}): Promise<void> {
    await this.prisma.auditLog.create({
      data: {
        event,
        actorCode: input.actorCode ?? '',
        detail: (input.detail ?? '').slice(0, 300),
        ipAddress: (input.ipAddress ?? '').slice(0, 60),
        userId: input.userId ?? null,
      },
    });
  }

  async recent(limit = 20) {
    return this.prisma.auditLog.findMany({
      orderBy: { createdAt: 'desc' },
      take: Math.min(Math.max(limit, 1), 100),
    });
  }
}
