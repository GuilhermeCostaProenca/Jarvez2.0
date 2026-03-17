import { NextResponse } from 'next/server';
import { randomBytes } from 'crypto';

const ONENOTE_CLIENT_ID = process.env.ONENOTE_CLIENT_ID ?? '';
const ONENOTE_REDIRECT_URI = process.env.ONENOTE_REDIRECT_URI ?? '';
const ONENOTE_SCOPES = process.env.ONENOTE_SCOPES ?? 'offline_access User.Read Notes.ReadWrite';
const STATE_COOKIE = 'jarvez_onenote_oauth_state';
const ONENOTE_AUTHORIZE_URL = 'https://login.microsoftonline.com/common/oauth2/v2.0/authorize';

export const runtime = 'nodejs';

function resolveRedirectUri(request: Request): string {
  const configured = ONENOTE_REDIRECT_URI.trim();
  if (configured) return configured;
  const origin = new URL(request.url).origin;
  return `${origin}/api/onenote/callback`;
}

export async function GET(request: Request) {
  if (!ONENOTE_CLIENT_ID) {
    return new NextResponse('ONENOTE_CLIENT_ID not configured', { status: 500 });
  }

  const redirectUri = resolveRedirectUri(request);
  const state = randomBytes(18).toString('hex');
  const params = new URLSearchParams({
    client_id: ONENOTE_CLIENT_ID,
    response_type: 'code',
    redirect_uri: redirectUri,
    response_mode: 'query',
    scope: ONENOTE_SCOPES,
    state,
  });

  const authorizeUrl = `${ONENOTE_AUTHORIZE_URL}?${params.toString()}`;
  const response = NextResponse.redirect(authorizeUrl);
  response.cookies.set(STATE_COOKIE, state, {
    httpOnly: true,
    sameSite: 'lax',
    secure: false,
    path: '/',
    maxAge: 600,
  });
  return response;
}
