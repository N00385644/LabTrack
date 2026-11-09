import { Controller, Get, Param, Query, UseGuards } from '@nestjs/common';
import { AuthGuard } from '@nestjs/passport';
import { ApiBearerAuth, ApiTags } from '@nestjs/swagger';
import { EquipmentService } from './equipment.service';

@ApiTags('equipment')
@ApiBearerAuth()
@UseGuards(AuthGuard('jwt'))
@Controller('equipment')
export class EquipmentController {
  constructor(private readonly equipmentService: EquipmentService) {}

  @Get()
  findAll(@Query('category') category?: string) {
    return this.equipmentService.findAll(category);
  }

  @Get('available')
  findAvailable() {
    return this.equipmentService.findAvailable();
  }

  @Get('stats')
  stats() {
    return this.equipmentService.stats();
  }

  @Get(':id')
  findOne(@Param('id') id: string) {
    return this.equipmentService.findOne(id);
  }
}
