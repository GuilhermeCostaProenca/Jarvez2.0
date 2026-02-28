import { NextResponse } from 'next/server';
import { randomBytes } from 'crypto';

const SPOTIFY_CLIENT_ID = process.env.SPOTIFY_CLIENT_ID ?? '';
const SPOTIFY_REDIRECT_URI = process.env.SPOTIFY_REDIRECT_URI ?? '';
const SPOTIFY_SCOPES =
  process.env.SPOTIFY_SCOPES ??
  'user-read-playback-state user-modify-playback-state user-read-currently-playing playlist-modify-private playlist-modify-public user-top-read';
const STATE_COOKIE = 'jarvez_spotify_oauth_state';
export const runtime = 'nodejs';

function resolveRedirectUri(request: Request): string {
  const configured = SPOTIFY_REDIRECT_URI.trim();
  if (configured) return configured;
  const origin = new URL(request.url).origin;
  return `${origin}/api/spotify/callback`;
}

export async function GET(request: Request) {
  if (!SPOTIFY_CLIENT_ID) {
    return new NextResponse('SPOTIFY_CLIENT_ID not configured', { status: 500 });
  }

  const redirectUri = resolveRedirectUri(request);
  const state = randomBytes(18).toString('hex');
  const params = new URLSearchParams({
    client_id: SPOTIFY_CLIENT_ID,
    response_type: 'code',
    redirect_uri: redirectUri,
    scope: SPOTIFY_SCOPES,
    state,
    show_dialog: 'true',
  });

  const authorizeUrl = `https://accounts.spotify.com/authorize?${params.toString()}`;
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
