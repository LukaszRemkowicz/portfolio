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

export function logRequest(info, requestId) {
  console.log(
    JSON.stringify({
      ts: getTimestamp(),
      service: 'frontend-ssr',
      request_id: requestId,
      ...info,
    })
  );
}
