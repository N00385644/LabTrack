import { Transform } from 'class-transformer';
import {
  IsEmail,
  IsIn,
  IsOptional,
  IsString,
  Matches,
  MaxLength,
  MinLength,
} from 'class-validator';

export class CreateUserDto {
  @Transform(({ value }) => (typeof value === 'string' ? value.trim().toUpperCase() : value))
  @IsString()
  @MinLength(4, { message: 'El código debe tener al menos 4 caracteres.' })
  @MaxLength(20, { message: 'El código no puede superar los 20 caracteres.' })
  @Matches(/^[A-Z0-9]+$/, {
    message: 'El código solo admite letras y números, sin espacios.',
  })
  code!: string;

  @Transform(({ value }) => (typeof value === 'string' ? value.trim() : value))
  @IsString()
  @MinLength(3, { message: 'El nombre completo es obligatorio.' })
  @MaxLength(120, { message: 'El nombre completo no puede superar los 120 caracteres.' })
  fullName!: string;

  @IsOptional()
  @Transform(({ value }) => (typeof value === 'string' ? value.trim() : value))
  @IsEmail({}, { message: 'El correo electrónico no es válido.' })
  @MaxLength(120)
  email?: string;

  @IsString()
  @MinLength(8, { message: 'La contraseña debe tener al menos 8 caracteres.' })
  @MaxLength(72, { message: 'La contraseña no puede superar los 72 caracteres.' })
  password!: string;

  @IsIn(['STUDENT', 'ADMIN'], { message: 'El rol debe ser STUDENT o ADMIN.' })
  role!: 'STUDENT' | 'ADMIN';
}
