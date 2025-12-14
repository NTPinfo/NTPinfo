/**
 * Simplifies error messages to show user-friendly versions
 * @param errorMessage - The full error message string
 * @returns A simplified, user-friendly error message
 */
export function simplifyErrorMessage(errorMessage: string | null | undefined): string {
  if (!errorMessage) {
    return '';
  }

  const error = errorMessage.toLowerCase();

  // Check for timeout errors
  if (error.includes('timeout') || error.includes('i/o timeout')) {
    return 'Measurement timeout';
  }

  // Check for connection errors
  if (error.includes('connection refused') || error.includes('connection reset')) {
    return 'Connection refused';
  }

  if (error.includes('connection') && error.includes('error')) {
    return 'Connection error';
  }

  // Check for network errors
  if (error.includes('network') || error.includes('network is unreachable')) {
    return 'Network error';
  }

  // Check for DNS errors
  if (error.includes('dns') || error.includes('no such host') || error.includes('name resolution')) {
    return 'DNS resolution failed';
  }

  // Check for permission errors
  if (error.includes('permission denied') || error.includes('access denied')) {
    return 'Permission denied';
  }

  // Check for server errors
  if (error.includes('server error') || error.includes('500')) {
    return 'Server error';
  }

  // Check for not found errors
  if (error.includes('not found') || error.includes('404')) {
    return 'Not found';
  }

  // Check for rate limit errors
  if (error.includes('rate limit') || error.includes('too many requests')) {
    return 'Rate limit exceeded';
  }

  // Check for RIPE probe availability errors (when no probes match the criteria)
  // Error format: ... 'pointer': '/probes' ... 'This list may not be empty'
  if (error.includes('/probes') && error.includes('may not be empty')) {
    return 'RIPE measurement failed: No probes available for the specified requirements';
  }

  // If no pattern matches, return the first part of the error (before colon if present)
  // This gives a more readable error without all the technical details
  const colonIndex = errorMessage.indexOf(':');
  if (colonIndex > 0 && colonIndex < 50) {
    // Only use the part before colon if it's reasonable length
    const beforeColon = errorMessage.substring(0, colonIndex).trim();
    // Capitalize first letter
    return beforeColon.charAt(0).toUpperCase() + beforeColon.slice(1);
  }

  // If error is too long, truncate it
  if (errorMessage.length > 100) {
    return errorMessage.substring(0, 100).trim() + '...';
  }

  // Return as-is if it's already short and readable
  return errorMessage;
}

