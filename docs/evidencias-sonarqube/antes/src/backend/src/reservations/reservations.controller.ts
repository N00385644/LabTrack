import {
  Body,
  Controller,
  Get,
  Post,
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
import { CreateReservationDto } from './dto/create-reservation.dto';
import { ReservationsService } from './reservations.service';

@ApiTags('reservations')
@ApiBearerAuth()
@UseGuards(AuthGuard('jwt'), RolesGuard)
@Controller('reservations')
export class ReservationsController {
  constructor(private readonly reservationsService: ReservationsService) {}

  @Post()
  @Roles(Role.STUDENT)
  create(
    @Req() request: Request & { user: AuthUser },
    @Body() dto: CreateReservationDto,
  ) {
    return this.reservationsService.create(request.user.id, dto, request.ip ?? '');
  }

  @Get('me')
  @Roles(Role.STUDENT)
  findMine(@Req() request: Request & { user: AuthUser }) {
    return this.reservationsService.findMine(request.user.id);
  }
}
