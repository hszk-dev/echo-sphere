/**
 * Result type for handling expected errors without exceptions.
 * Use this for operations that can fail in expected ways.
 */
export type Result<T, E = Error> = { success: true; data: T } | { success: false; error: E };

/**
 * Create a successful result.
 */
export function ok<T>(data: T): Result<T, never> {
  return { success: true, data };
}

/**
 * Create a failed result.
 */
export function err<E>(error: E): Result<never, E> {
  return { success: false, error };
}

/**
 * Check if result is successful.
 */
export function isOk<T, E>(result: Result<T, E>): result is { success: true; data: T } {
  return result.success;
}

/**
 * Check if result is an error.
 */
export function isErr<T, E>(result: Result<T, E>): result is { success: false; error: E } {
  return !result.success;
}
