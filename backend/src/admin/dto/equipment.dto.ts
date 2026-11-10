import { Transform } from 'class-transformer';
import {
  IsIn,
  IsOptional,
  IsString,
  IsUrl,
  Matches,
  MaxLength,
  MinLength,
} from 'class-validator';

const CATEGORY_VALUES = ['Cómputo', 'Electrónica', 'Redes'] as const;

export class CreateEquipmentDto {
  @Transform(({ value }) => (typeof value === 'string' ? value.trim() : value))
  @IsString()
  @MinLength(3, { message: 'El nombre del equipo es obligatorio.' })
  @MaxLength(120)
  name!: string;

  @Transform(({ value }) => (typeof value === 'string' ? value.trim().toUpperCase() : value))
  @IsString()
  @MinLength(3, { message: 'El código de inventario es obligatorio.' })
  @MaxLength(30)
  @Matches(/^[A-Z0-9-]+$/, {
    message: 'El código de inventario solo admite letras, números y guiones.',
  })
  inventoryCode!: string;

  @IsIn(CATEGORY_VALUES, { message: 'La categoría debe ser Cómputo, Electrónica o Redes.' })
  category!: string;

  @IsOptional()
  @Transform(({ value }) => (typeof value === 'string' ? value.trim() : value))
  @IsString()
  @MaxLength(300)
  description?: string;

  @IsOptional()
  @Transform(({ value }) => (typeof value === 'string' ? value.trim() : value))
  @IsString()
  @MaxLength(120)
  location?: string;

  @IsOptional()
  @Transform(({ value }) => (typeof value === 'string' ? value.trim() : value))
  @IsUrl({}, { message: 'La foto debe ser una URL válida.' })
  @MaxLength(300)
  photoUrl?: string;

  @IsOptional()
  @Transform(({ value }) => (typeof value === 'string' ? value.trim() : value))
  @IsString()
  @MaxLength(200)
  qrCode?: string;
}

export class UpdateEquipmentDto {
  @IsOptional()
  @Transform(({ value }) => (typeof value === 'string' ? value.trim() : value))
  @IsString()
  @MinLength(3, { message: 'El nombre del equipo es obligatorio.' })
  @MaxLength(120)
  name?: string;

  @IsOptional()
  @Transform(({ value }) => (typeof value === 'string' ? value.trim().toUpperCase() : value))
  @IsString()
  @MinLength(3, { message: 'El código de inventario es obligatorio.' })
  @MaxLength(30)
  @Matches(/^[A-Z0-9-]+$/, {
    message: 'El código de inventario solo admite letras, números y guiones.',
  })
  inventoryCode?: string;

  @IsOptional()
  @IsIn(CATEGORY_VALUES, { message: 'La categoría debe ser Cómputo, Electrónica o Redes.' })
  category?: string;

  @IsOptional()
  @Transform(({ value }) => (typeof value === 'string' ? value.trim() : value))
  @IsString()
  @MaxLength(300)
  description?: string;

  @IsOptional()
  @Transform(({ value }) => (typeof value === 'string' ? value.trim() : value))
  @IsString()
  @MaxLength(120)
  location?: string;

  @IsOptional()
  @Transform(({ value }) => (typeof value === 'string' ? value.trim() : value))
  @IsUrl({}, { message: 'La foto debe ser una URL válida.' })
  @MaxLength(300)
  photoUrl?: string;

  @IsOptional()
  @Transform(({ value }) => (typeof value === 'string' ? value.trim() : value))
  @IsString()
  @MaxLength(200)
  qrCode?: string;
}
