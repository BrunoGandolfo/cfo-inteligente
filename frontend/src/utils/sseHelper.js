export function parseSSEEvent(rawEvent) {
  if (!rawEvent?.trim()) {
    return null;
  }

  const lines = rawEvent.split('\n');
  let event = 'message';
  const dataLines = [];

  for (const line of lines) {
    if (line.startsWith('event:')) {
      event = line.slice(6).trim();
    } else if (line.startsWith('data:')) {
      dataLines.push(line.slice(5).trim());
    }
  }

  const data = dataLines.join('\n');
  if (!data) {
    return null;
  }

  return { event, data };
}

export async function readSSEStream(stream, onEvent) {
  if (!stream) {
    throw new Error('Streaming no disponible');
  }

  const reader = stream.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { value, done } = await reader.read();
    if (done) {
      break;
    }

    buffer += decoder.decode(value, { stream: true });
    const rawEvents = buffer.split('\n\n');
    buffer = rawEvents.pop() || '';

    for (const rawEvent of rawEvents) {
      const parsed = parseSSEEvent(rawEvent);
      if (parsed) {
        await onEvent(parsed);
      }
    }
  }

  buffer += decoder.decode();
  if (buffer.trim()) {
    const parsed = parseSSEEvent(buffer);
    if (parsed) {
      await onEvent(parsed);
    }
  }
}
