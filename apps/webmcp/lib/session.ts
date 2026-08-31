import { NextRequest, NextResponse } from 'next/server';
export const SESSION_COOKIE = 'repog_demo_session';
export function sessionId(request: NextRequest) { return request.cookies.get(SESSION_COOKIE)?.value || crypto.randomUUID(); }
export function isSameOrigin(request: NextRequest) {
  const origin = request.headers.get('origin');
  return origin === request.nextUrl.origin;
}
export function hasAcceptableBodySize(request: NextRequest, maxBytes = 16_384) {
  const rawLength = request.headers.get('content-length');
  if (!rawLength) return true;
  const length = Number(rawLength);
  return Number.isFinite(length) && length >= 0 && length <= maxBytes;
}
export function withSession(response: NextResponse, id: string) {
  response.cookies.set(SESSION_COOKIE, id, { httpOnly: true, sameSite: 'strict', secure: process.env.NODE_ENV === 'production', path: '/', maxAge: 60 * 60 * 6 });
  return response;
}
