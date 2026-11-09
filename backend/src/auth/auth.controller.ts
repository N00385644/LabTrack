import {
  Body,
  Controller,
  Get,
  HttpCode,
  Post,
  Req,
  UseGuards,
} from '@nestjs/common';
import { AuthGuard } from '@nestjs/passport';
import { ApiBearerAuth, ApiTags } from '@nestjs/swagger';
import { Request } from 'express';
import { AuthUser } from '../common/types/auth-user';
import { AuthService } from './auth.service';
import { LoginDto } from './dto/login.dto';

@ApiTags('auth')
@Controller('auth')
export class AuthController {
  constructor(private readonly authService: AuthService) {}

  @Post('login')
  @HttpCode(200)
  login(@Body() dto: LoginDto, @Req() request: Request) {
    return this.authService.login(dto, request.ip ?? '');
  }

  @Get('me')
  @ApiBearerAuth()
  @UseGuards(AuthGuard('jwt'))
  me(@Req() request: Request & { user: AuthUser }) {
    return { user: request.user };
  }

  @Post('logout')
  @ApiBearerAuth()
  @HttpCode(200)
  @UseGuards(AuthGuard('jwt'))
  logout() {
    return { message: 'Sesión cerrada correctamente.' };
  }
}
