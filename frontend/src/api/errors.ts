export class AppError extends Error {
  constructor(
    public message: string,
    public statusCode?: number,
    public originalError?: unknown,
  ) {
    super(message);
    this.name = "AppError";
    Object.setPrototypeOf(this, AppError.prototype);
  }
}

export class NetworkError extends AppError {
  constructor(
    message: string = "Network connection issue. Please check your internet.",
    originalError?: unknown,
  ) {
    super(message, undefined, originalError);
    this.name = "NetworkError";
    Object.setPrototypeOf(this, NetworkError.prototype);
  }
}

export class ValidationError extends AppError {
  constructor(
    public errors: Record<string, string[]>,
    message: string = "Validation failed.",
    originalError?: unknown,
  ) {
    super(message, 400, originalError);
    this.name = "ValidationError";
    Object.setPrototypeOf(this, ValidationError.prototype);
  }
}

export class NotFoundError extends AppError {
  constructor(
    message: string = "The requested resource was not found.",
    originalError?: unknown,
  ) {
    super(message, 404, originalError);
    this.name = "NotFoundError";
    Object.setPrototypeOf(this, NotFoundError.prototype);
  }
}

export class ServerError extends AppError {
  constructor(
    message: string = "Internal server error. Please try again later.",
    statusCode: number = 500,
    originalError?: unknown,
  ) {
    super(message, statusCode, originalError);
    this.name = "ServerError";
    Object.setPrototypeOf(this, ServerError.prototype);
  }
}

export class UnauthorizedError extends AppError {
  constructor(
    message: string = "Unauthorized access. Please log in.",
    statusCode: number = 401,
    originalError?: unknown,
  ) {
    super(message, statusCode, originalError);
    this.name = "UnauthorizedError";
    Object.setPrototypeOf(this, UnauthorizedError.prototype);
  }
}
