import { ArgumentsHost, Catch, ExceptionFilter, HttpException } from '@nestjs/common';
import type { Response } from 'express';

// CONTRACT.md requires a specific error shape ({ "error": "<message>" }) —
// Nest's own default HttpException envelope is { statusCode, message,
// error: "<HTTP status phrase>" }, which doesn't match. Rewrites every
// HttpException (NotFoundException, BadRequestException, ...) thrown by a
// controller into the contract's shape, so controllers can just
// `throw new NotFoundException('...')` and stay framework-idiomatic.
@Catch(HttpException)
export class ContractErrorFilter implements ExceptionFilter {
  catch(exception: HttpException, host: ArgumentsHost) {
    const res = host.switchToHttp().getResponse<Response>();
    const status = exception.getStatus();
    const body = exception.getResponse();
    const message = typeof body === 'string' ? body : (body as { message?: string | string[] }).message;
    res.status(status).json({ error: Array.isArray(message) ? message[0] : message });
  }
}
