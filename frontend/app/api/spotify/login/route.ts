import { NextResponse } from 'next/server';
import { createHmac, randomBytes } from 'crypto';

const SPOTIFY_CLIENT_ID = process.env.SPOTIFY_CLIENT_ID ?? '';
const SPOTIFY_REDIRECT_URI = process.env.SPOTIFY_REDIRECT_URI ?? '';
const SPOTIFY_SCOPES =
  process.env.SPOTIFY_SCOPES ??
  'user-read-playback-state user-modify-playback-state user-read-currently-playing playlist-modify-private playlist-modify-public user-top-read';
export const runtime = 'nodejs';

function resolveStateSecret(): string {
  return process.env.SPOTIFY_STATE_SECRET?.trim() || SPOTIFY_CLIENT_SECRET_FALLBACK || SPOTIFY_CLIENT_ID;
}

const SPOTIFY_CLIENT_SECRET_FALLBACK = process.env.SPOTIFY_CLIENT_SECRET ?? '';

function createSignedState(): string {
  const nonce = randomBytes(18).toString('hex');
  const signature = createHmac('sha256', resolveStateSecret()).update(nonce).digest('hex');
  return `${nonce}.${signature}`;
}

function resolveLoopbackOrigin(request: Request): string {
  const incoming = new URL(request.url);
  const isLocalHost = incoming.hostname === 'localhost' || incoming.hostname === '127.0.0.1';
  if (!isLocalHost) return incoming.origin;
  return `${incoming.protocol}//127.0.0.1${incoming.port ? `:${incoming.port}` : ''}`;
}

function resolveRedirectUri(request: Request): string {
  const configured = SPOTIFY_REDIRECT_URI.trim();
  const origin = resolveLoopbackOrigin(request);
  if (configured) {
    const configuredUrl = new URL(configured);
    const isConfiguredLocal =
      configuredUrl.hostname === 'localhost' || configuredUrl.hostname === '127.0.0.1';
    const incomingUrl = new URL(request.url);
    const isIncomingLocal =
      incomingUrl.hostname === 'localhost' || incomingUrl.hostname === '127.0.0.1';
    if (!isConfiguredLocal || !isIncomingLocal) return configured;
    const targetPath = configuredUrl.pathname || '/api/spotify/callback';
    return `${origin}${targetPath}`;
  }
  return `${origin}/api/spotify/callback`;
}

export async function GET(request: Request) {
  if (!SPOTIFY_CLIENT_ID) {
    return new NextResponse('SPOTIFY_CLIENT_ID not configured', { status: 500 });
  }

  const redirectUri = resolveRedirectUri(request);
  const state = createSignedState();
  const params = new URLSearchParams({
    client_id: SPOTIFY_CLIENT_ID,
    response_type: 'code',
    redirect_uri: redirectUri,
    scope: SPOTIFY_SCOPES,
    state,
    show_dialog: 'true',
  });

  const authorizeUrl = `https://accounts.spotify.com/authorize?${params.toString()}`;
  return NextResponse.redirect(authorizeUrl);
}
