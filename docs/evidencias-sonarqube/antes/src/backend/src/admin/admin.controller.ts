import {
  Body,
  Controller,
  Get,
  Param,
  Patch,
  Query,
  Req,
  UseGuards,
} from '@nestjs/common';
import { AuthGuard } from '@nestjs/passport';
import { ApiBearerAuth, ApiTags } from '@nestjs/swagger';
import { Role } from '@prisma/client';
import { Request } from 'express';
import { Roles } from '../common/decorators/roles.decorator';
import { RolesGuard } from '../common/guards/roles.guard';
import { AuthUser } from '../common/types/auth-user';
import { AdminService } from './admin.service';
import { RejectReservationDto } from './dto/reject-reservation.dto';

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
}
