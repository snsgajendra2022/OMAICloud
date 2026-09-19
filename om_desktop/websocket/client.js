/** Connect to OM companion realtime hub. */
export function connectCompanion(sessionId = 'desktop') {
  const proto = location.protocol === 'https:' ? 'wss' : 'ws';
  const url = `${proto}://${location.hostname || '127.0.0.1'}:8767/api/companion/ws/${sessionId}`;
  const ws = new WebSocket(url);
  ws.addEventListener('open', () => ws.send(JSON.stringify({ event_type: 'hello', payload: { client: 'om_desktop' } })));
  return ws;
}
