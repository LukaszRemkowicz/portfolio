function getTimestamp() {
  // Use en-CA as it provides YYYY-MM-DD which is a good base for ISO
  return new Intl.DateTimeFormat('en-CA', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false,
    fractionalSecondDigits: 3,
  })
    .format(new Date())
    .replace(', ', 'T');
}

function sanitize(value) {
  if (value === null || value === undefined) {
    return '';
  }

  if (typeof value === 'string') {
    return value.replace(/\n/g, ' ').replace(/\r/g, ' ');
  }

  if (
    typeof value === 'number' ||
    typeof value === 'boolean' ||
    Array.isArray(value)
  ) {
    return value;
  }

  if (value instanceof Error) {
    return {
      name: value.name,
      message: value.message,
      stack: value.stack,
    };
  }

  return value;
}

function writeJsonLog(level, payload) {
  const normalized = {
    timestamp: getTimestamp(),
    service: 'frontend-ssr',
    level,
    ...payload,
  };

  const line = JSON.stringify(normalized);
  if (level === 'ERROR') {
    console.error(line);
    return;
  }
  console.log(line);
}

export function logEvent(payload, requestId) {
  writeJsonLog('INFO', {
    request_id: requestId || '',
    ...payload,
  });
}

export function logWarning(payload, requestId) {
  writeJsonLog('WARNING', {
    request_id: requestId || '',
    ...payload,
  });
}

export function logError(payload, requestId) {
  writeJsonLog('ERROR', {
    request_id: requestId || '',
    ...payload,
  });
}

export function logRequest(info, requestId) {
  logEvent(info, requestId);
}

export function toErrorPayload(error) {
  if (error instanceof Error) {
    return {
      error_name: error.name,
      error_message: sanitize(error.message),
      error_stack: sanitize(error.stack || ''),
    };
  }

  return {
    error_message: sanitize(String(error)),
  };
}
