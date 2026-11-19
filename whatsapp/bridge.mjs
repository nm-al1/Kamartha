import http from 'node:http';
import { timingSafeEqual } from 'node:crypto';
import { mkdirSync } from 'node:fs';
import { join } from 'node:path';
import QRCode from 'qrcode';
import WhatsApp from 'whatsapp-web.js';
import { DeliveryLedger } from './ledger.mjs';

const { Client, LocalAuth } = WhatsApp;
const token = process.env.WHATSAPP_BRIDGE_TOKEN ?? '';
if (Buffer.byteLength(token) < 32) throw new Error('WHATSAPP_BRIDGE_TOKEN must contain at least 32 bytes.');
const allowed = new Set((process.env.WHATSAPP_ALLOWED_NUMBERS ?? '').split(',').map(n => n.trim()).filter(Boolean));
if ([...allowed].some(n => !/^62\d{8,13}$/.test(n))) throw new Error('Allowlist must contain Indonesian international numbers, digits only.');
const dataDir = process.env.WHATSAPP_DATA_DIR ?? './.state';
mkdirSync(dataDir, { recursive: true, mode: 0o700 });
const ledger = new DeliveryLedger(join(dataDir, 'delivery-state.json'));
let ready = false, qr = null, state = 'STARTING', qrVersion = 0;
const client = new Client({
  authStrategy: new LocalAuth({ dataPath: join(dataDir, 'session') }),
  puppeteer: {
    headless: true,
    ...(process.env.CHROME_PATH ? { executablePath: process.env.CHROME_PATH } : {}),
    ...(process.env.CHROME_NO_SANDBOX === 'true' ? { args: ['--no-sandbox', '--disable-setuid-sandbox'] } : {}),
  },
});
client.on('qr', async value => {
  const version = ++qrVersion;
  state = 'SCAN_QR';
  qr = null;
  try {
    const image = await QRCode.toDataURL(value);
    if (state === 'SCAN_QR' && version === qrVersion) qr = image;
  } catch {
    if (state === 'SCAN_QR' && version === qrVersion) state = 'QR_FAILED';
  }
});
client.on('ready', () => { ready = true; qr = null; state = 'READY'; console.log('WhatsApp prototype ready.'); });
client.on('disconnected', () => { ready = false; qr = null; state = 'DISCONNECTED'; });
client.on('auth_failure', () => { ready = false; qr = null; state = 'AUTH_FAILED'; });

function reply(response, status, data) {
  response.writeHead(status, { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' });
  response.end(JSON.stringify(data));
}

async function deliver(number, body, rememberMessageId) {
  const recipient = await client.getNumberId(number);
  if (!recipient) throw new Error('NUMBER_NOT_REGISTERED');
  const message = await client.sendMessage(recipient._serialized, body, { sendSeen: false });
  const id = message.id._serialized;
  rememberMessageId(id);
  if (message.ack >= 1) return { id, ack: message.ack };
  const ack = await new Promise(resolve => {
    const finish = value => { clearTimeout(timer); client.off('message_ack', listener); resolve(value); };
    const listener = (msg, value) => { if (msg.id._serialized === id && value >= 1) finish(value); };
    const timer = setTimeout(() => finish(0), 10000);
    client.on('message_ack', listener);
  });
  return { id, ack };
}

const server = http.createServer(async (request, response) => {
  const supplied = Buffer.from(request.headers.authorization ?? '');
  const expected = Buffer.from(`Bearer ${token}`);
  if (supplied.length !== expected.length || !timingSafeEqual(supplied, expected)) return reply(response, 401, { error: 'UNAUTHORIZED' });
  try {
    if (request.method === 'GET' && request.url === '/status') return reply(response, 200, { ready, qr, state });
    const match = /^\/messages\/([a-f0-9-]{36})$/.exec(request.url ?? '');
    if (request.method === 'GET' && match) {
      let receipt = ledger.receipt(match[1]);
      if (ready && receipt.message_id && receipt.state === 'UNKNOWN') {
        const message = await client.getMessageById(receipt.message_id);
        if (message?.ack >= 1) receipt = ledger.acknowledge(match[1], receipt.message_id);
      }
      return reply(response, 200, receipt);
    }
    if (request.method !== 'POST' || request.url !== '/send') return reply(response, 404, { error: 'NOT_FOUND' });
    let body = '';
    for await (const chunk of request) {
      body += chunk.toString('utf8');
      if (Buffer.byteLength(body) > 16384) return reply(response, 413, { error: 'TOO_LARGE' });
    }
    const { key, number, message } = JSON.parse(body);
    if (typeof key !== 'string' || !/^[a-f0-9-]{36}$/.test(key) || !allowed.has(number)
      || typeof message !== 'string' || message.length > 4000 || !message.startsWith('[DEMO KAMARTHA]')) {
      return reply(response, 422, { error: 'DEMO_ALLOWLIST_REQUIRED' });
    }
    if (!ready) return reply(response, 409, { error: 'NOT_READY' });
    return reply(response, 200, await ledger.send(key, number, message, deliver));
  } catch {
    return reply(response, 409, { error: 'DELIVERY_UNCERTAIN' });
  }
});
server.requestTimeout = 20000;
server.listen(Number(process.env.PORT ?? 3001), process.env.BRIDGE_HOST ?? '127.0.0.1');
client.initialize().catch(() => { state = 'START_FAILED'; console.error('WhatsApp startup failed; check Chrome and session.'); });
process.on('SIGTERM', async () => { server.close(); await client.destroy(); process.exit(0); });
