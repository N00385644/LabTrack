import { Transform } from 'class-transformer';
import { IsString, MaxLength, MinLength } from 'class-validator';

export class RejectReservationDto {
  @Transform(({ value }) => (typeof value === 'string' ? value.trim() : value))
  @IsString()
  @MinLength(5, { message: 'Debes ingresar un motivo de rechazo de al menos 5 caracteres.' })
  @MaxLength(300, { message: 'El motivo de rechazo no puede superar los 300 caracteres.' })
  reason!: string;
}
