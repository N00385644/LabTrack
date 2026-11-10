import { Transform } from 'class-transformer';
import { IsString, MaxLength, MinLength } from 'class-validator';

export class LiftPenaltyDto {
  @Transform(({ value }) => (typeof value === 'string' ? value.trim() : value))
  @IsString()
  @MinLength(5, { message: 'Debes justificar el levantamiento con al menos 5 caracteres.' })
  @MaxLength(300, { message: 'La justificación no puede superar los 300 caracteres.' })
  justification!: string;
}
