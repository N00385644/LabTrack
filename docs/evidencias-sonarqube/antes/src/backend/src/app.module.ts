import { Module } from '@nestjs/common';
import { ConfigModule } from '@nestjs/config';
import { AdminModule } from './admin/admin.module';
import { AuditModule } from './audit/audit.module';
import { AuthModule } from './auth/auth.module';
import { EquipmentModule } from './equipment/equipment.module';
import { HealthController } from './health.controller';
import { PrismaModule } from './prisma/prisma.module';
import { ReservationsModule } from './reservations/reservations.module';

@Module({
  imports: [
    ConfigModule.forRoot({
      isGlobal: true,
      envFilePath: ['.env', '.env.test'],
      validate: (config: Record<string, unknown>) => {
        if (!config.DATABASE_URL) {
          throw new Error('Falta la variable de entorno DATABASE_URL.');
        }
        if (!config.JWT_SECRET) {
          throw new Error('Falta la variable de entorno JWT_SECRET.');
        }
        return config;
      },
    }),
    PrismaModule,
    AuditModule,
    AuthModule,
    EquipmentModule,
    ReservationsModule,
    AdminModule,
  ],
  controllers: [HealthController],
})
export class AppModule {}
