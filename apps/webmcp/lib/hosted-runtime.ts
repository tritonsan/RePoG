import { env } from 'cloudflare:workers';

const encoder = new TextEncoder();

function runtimeEnv() {
  const values = env as unknown as Record<string, unknown>;
  const baseUrl = String(values.REPOG_RUNTIME_URL || '').replace(/\/$/, '');
  const secret = String(values.REPOG_RUNTIME_SHARED_SECRET || '');
  if (!baseUrl || !secret) throw new Error('hosted_runtime_not_configured');
  return { baseUrl, secret };
}

async function hmac(secret: string, message: string) {
  const key = await crypto.subtle.importKey('raw', encoder.encode(secret), { name: 'HMAC', hash: 'SHA-256' }, false, ['sign']);
  const signature = await crypto.subtle.sign('HMAC', key, encoder.encode(message));
  return Array.from(new Uint8Array(signature), (byte) => byte.toString(16).padStart(2, '0')).join('');
}

async function digest(body: string) {
  const bytes = await crypto.subtle.digest('SHA-256', encoder.encode(body));
  return Array.from(new Uint8Array(bytes), (byte) => byte.toString(16).padStart(2, '0')).join('');
}

export async function hostedRequest<T>(path: string, method: 'GET' | 'POST' = 'GET', payload?: unknown): Promise<T> {
  const { baseUrl, secret } = runtimeEnv();
  const body = payload === undefined ? '' : JSON.stringify(payload);
  const timestamp = Math.floor(Date.now() / 1000).toString();
  const nonce = crypto.randomUUID();
  const canonical = `${timestamp}\n${nonce}\n${method}\n${path}\n${await digest(body)}`;
  const response = await fetch(`${baseUrl}${path}`, {
    method,
    headers: { 'Content-Type': 'application/json', 'X-RePoG-Timestamp': timestamp, 'X-RePoG-Nonce': nonce, 'X-RePoG-Signature': await hmac(secret, canonical) },
    body: body || undefined,
  });
  const result = await response.json() as T & { failure_reason?: string };
  if (!response.ok) throw new Error(result.failure_reason || `Hosted runtime returned ${response.status}.`);
  return result;
}
