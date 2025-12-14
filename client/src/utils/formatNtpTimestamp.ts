/**
 * Converts an NTP timestamp (large number) to a human-readable UTC date string
 * @param ntpTimestamp - The NTP timestamp as a large number or string (e.g., 17067606958075056177)
 * @returns A formatted UTC date string (e.g., "2024-02-01 12:30:45.123456 UTC") or "N/A" if invalid
 */
export function formatNtpTimestampToUTC(ntpTimestamp: number | string | bigint | null | undefined): string {
  if (!ntpTimestamp || (typeof ntpTimestamp === 'number' && (isNaN(ntpTimestamp) || ntpTimestamp <= 0))) {
    return 'N/A';
  }

  try {
    // NTP timestamp format: first 32 bits are seconds, remaining bits are fraction
    const NTP_TO_UNIX_EPOCH_OFFSET = BigInt(2208988800); // seconds between 1900-01-01 and 1970-01-01
    const TWO_POWER_32 = BigInt(2) ** BigInt(32);
    
    // Convert to BigInt for precision with very large numbers
    let ntpBigInt: bigint;
    if (typeof ntpTimestamp === 'bigint') {
      ntpBigInt = ntpTimestamp;
    } else if (typeof ntpTimestamp === 'string') {
      ntpBigInt = BigInt(ntpTimestamp);
    } else {
      // For numbers, check if they're safe for normal operations
      if (ntpTimestamp > Number.MAX_SAFE_INTEGER) {
        ntpBigInt = BigInt(Math.floor(ntpTimestamp));
      } else {
        ntpBigInt = BigInt(ntpTimestamp);
      }
    }
    
    // Extract seconds and fraction parts (32 bits each)
    const seconds = ntpBigInt / TWO_POWER_32;
    const fraction = ntpBigInt % TWO_POWER_32;
    
    // Convert to Unix timestamp (seconds since 1970-01-01)
    const unixSecondsBigInt = seconds - NTP_TO_UNIX_EPOCH_OFFSET;
    const unixSeconds = Number(unixSecondsBigInt);
    const fractionNum = Number(fraction);
    const unixFraction = fractionNum / Number(TWO_POWER_32);
    
    // Convert to Date object (in milliseconds)
    const date = new Date(unixSeconds * 1000);
    
    // Format as UTC
    const year = date.getUTCFullYear();
    const month = String(date.getUTCMonth() + 1).padStart(2, '0');
    const day = String(date.getUTCDate()).padStart(2, '0');
    const hours = String(date.getUTCHours()).padStart(2, '0');
    const minutes = String(date.getUTCMinutes()).padStart(2, '0');
    const secs = String(date.getUTCSeconds()).padStart(2, '0');
    
    // Get microseconds from the fraction part
    const microseconds = Math.floor(unixFraction * 1000000);
    const microsecondsStr = String(microseconds).padStart(6, '0');
    
    return `${year}-${month}-${day} ${hours}:${minutes}:${secs}.${microsecondsStr} UTC`;
  } catch (error) {
    console.error('Error formatting NTP timestamp:', error, ntpTimestamp);
    return 'N/A';
  }
}

