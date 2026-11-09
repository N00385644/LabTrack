import { HttpException, HttpStatus } from '@nestjs/common';

export class DomainException extends HttpException {
  constructor(
    message: string,
    status: HttpStatus = HttpStatus.BAD_REQUEST,
    code = 'BUSINESS_RULE',
  ) {
    super({ statusCode: status, message, code }, status);
  }
}
