/**
 * Structured logger for frontend.
 * In production, this would be configured to send logs to a service.
 */

type LogLevel = "debug" | "info" | "warn" | "error";

interface LogContext {
  [key: string]: unknown;
}

interface Logger {
  debug: (message: string, context?: LogContext) => void;
  info: (message: string, context?: LogContext) => void;
  warn: (message: string, context?: LogContext) => void;
  error: (message: string, context?: LogContext) => void;
}

function createLogEntry(level: LogLevel, message: string, context?: LogContext): void {
  const entry = {
    timestamp: new Date().toISOString(),
    level,
    message,
    ...context,
  };

  switch (level) {
    case "debug":
      console.debug(JSON.stringify(entry));
      break;
    case "info":
      console.info(JSON.stringify(entry));
      break;
    case "warn":
      console.warn(JSON.stringify(entry));
      break;
    case "error":
      console.error(JSON.stringify(entry));
      break;
  }
}

export const logger: Logger = {
  debug: (message, context) => createLogEntry("debug", message, context),
  info: (message, context) => createLogEntry("info", message, context),
  warn: (message, context) => createLogEntry("warn", message, context),
  error: (message, context) => createLogEntry("error", message, context),
};
