import { IsNotEmpty, IsString, Matches } from 'class-validator';

export class CreateReservationDto {
  @IsString()
  @IsNotEmpty()
  equipmentId!: string;

  @Matches(/^\d{4}-\d{2}-\d{2}$/, { message: 'La fecha debe tener el formato YYYY-MM-DD.' })
  date!: string;

  @Matches(/^([01]\d|2[0-3]):[0-5]\d$/, { message: 'La hora de inicio debe tener el formato HH:MM.' })
  startTime!: string;

  @Matches(/^([01]\d|2[0-3]):[0-5]\d$/, { message: 'La hora de fin debe tener el formato HH:MM.' })
  endTime!: string;
}
