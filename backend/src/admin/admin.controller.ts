import {
  Body,
  Controller,
  Delete,
  Get,
  HttpCode,
  Param,
  Patch,
  Post,
  Query,
  Req,
  Res,
  UseGuards,
} from '@nestjs/common';
import { AuthGuard } from '@nestjs/passport';
import { ApiBearerAuth, ApiTags } from '@nestjs/swagger';
import { Role } from '@prisma/client';
import { Request, Response } from 'express';
import { Roles } from '../common/decorators/roles.decorator';
import { RolesGuard } from '../common/guards/roles.guard';
import { AuthUser } from '../common/types/auth-user';
import { AdminService } from './admin.service';
import { RejectReservationDto } from './dto/reject-reservation.dto';
import { CreateUserDto } from './dto/create-user.dto';
import { CreateEquipmentDto, UpdateEquipmentDto } from './dto/equipment.dto';
import { LiftPenaltyDto } from './dto/lift-penalty.dto';
import { ResetPasswordDto } from './dto/reset-password.dto';

@ApiTags('admin')
@ApiBearerAuth()
@UseGuards(AuthGuard('jwt'), RolesGuard)
@Roles(Role.ADMIN)
@Controller('admin')
export class AdminController {
  constructor(private readonly adminService: AdminService) {}

  @Get('reservations')
  listReservations(@Query('status') status?: string) {
    return this.adminService.listReservations(status);
  }

  @Get('stats')
  stats() {
    return this.adminService.stats();
  }

  @Get('dashboard')
  dashboard() {
    return this.adminService.dashboardStats();
  }

  @Get('users')
  users() {
    return this.adminService.listUsers();
  }

  @Post('users')
  createUser(@Body() dto: CreateUserDto, @Req() request: Request & { user: AuthUser }) {
    return this.adminService.createUser(dto, request.user);
  }

  @Patch('users/:id/reset-password')
  resetPassword(@Param('id') id: string, @Body() dto: ResetPasswordDto, @Req() request: Request & { user: AuthUser }) {
    return this.adminService.resetPassword(id, dto.password, request.user);
  }

  @Patch('users/:id/unlock')
  unlock(@Param('id') id: string, @Req() request: Request & { user: AuthUser }) {
    return this.adminService.unlockUser(id, request.user);
  }

  @Patch('users/:id/lift-penalty')
  liftPenalty(@Param('id') id: string, @Body() dto: LiftPenaltyDto, @Req() request: Request & { user: AuthUser }) {
    return this.adminService.liftPenalty(id, dto.justification, request.user);
  }

  @Get('equipment')
  equipment() {
    return this.adminService.listEquipment();
  }

  @Post('equipment')
  createEquipment(@Body() dto: CreateEquipmentDto, @Req() request: Request & { user: AuthUser }) {
    return this.adminService.createEquipment(dto, request.user);
  }

  @Patch('equipment/:id')
  updateEquipment(@Param('id') id: string, @Body() dto: UpdateEquipmentDto, @Req() request: Request & { user: AuthUser }) {
    return this.adminService.updateEquipment(id, dto, request.user);
  }

  @Delete('equipment/:id')
  deleteEquipment(@Param('id') id: string, @Req() request: Request & { user: AuthUser }) {
    return this.adminService.deleteEquipment(id, request.user);
  }

  @Get('audit')
  audit(@Query('limit') limit?: string) {
    const parsed = limit ? Number.parseInt(limit, 10) : 20;
    return this.adminService.recentAudit(Number.isNaN(parsed) ? 20 : parsed);
  }

  @Patch('reservations/:id/approve')
  approve(
    @Param('id') id: string,
    @Req() request: Request & { user: AuthUser },
  ) {
    return this.adminService.approve(id, request.user);
  }

  @Patch('reservations/:id/reject')
  reject(
    @Param('id') id: string,
    @Body() dto: RejectReservationDto,
    @Req() request: Request & { user: AuthUser },
  ) {
    return this.adminService.reject(id, request.user, dto.reason);
  }

  @Patch('reservations/:id/return')
  markReturned(
    @Param('id') id: string,
    @Req() request: Request & { user: AuthUser },
  ) {
    return this.adminService.markReturned(id, request.user);
  }

  @Get('reservations/:id/acta')
  async acta(@Param('id') id: string, @Res() response: Response) {
    const reservation = await this.adminService.findReservation(id);
    response.type('html').send(`<!doctype html><html lang="es"><head><meta charset="utf-8"><title>Acta de préstamo</title><style>body{font-family:Arial;max-width:760px;margin:40px auto}h1{color:#123}table{width:100%;border-collapse:collapse}td{border:1px solid #ddd;padding:8px}</style></head><body><h1>Acta de préstamo de equipo</h1><table><tr><td>Estudiante</td><td>${reservation.student.fullName} (${reservation.student.code})</td></tr><tr><td>Equipo</td><td>${reservation.equipment.name} - ${reservation.equipment.inventoryCode}</td></tr><tr><td>Fecha y horario</td><td>${reservation.date} ${reservation.startTime} - ${reservation.endTime}</td></tr></table><p>El estudiante declara recibir el equipo en las condiciones indicadas y se responsabiliza por su cuidado, uso correcto y devolución oportuna.</p><p>Firma del estudiante: ____________________</p><p>Firma del encargado: ____________________</p><script>window.print()</script></body></html>`);
  }

  @Post('scan')
  @HttpCode(200)
  scan(@Body() body: { code?: string; action?: 'DISPATCH' | 'RETURN' }, @Req() request: Request & { user: AuthUser }) {
    return this.adminService.scan(body.code ?? '', body.action ?? 'DISPATCH', request.user);
  }
}
