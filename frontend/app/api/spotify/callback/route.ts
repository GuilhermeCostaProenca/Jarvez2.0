import { NextResponse } from 'next/server';
import { mkdir, writeFile } from 'fs/promises';
import path from 'path';

const SPOTIFY_CLIENT_ID = process.env.SPOTIFY_CLIENT_ID ?? '';
const SPOTIFY_CLIENT_SECRET = process.env.SPOTIFY_CLIENT_SECRET ?? '';
const SPOTIFY_REDIRECT_URI = process.env.SPOTIFY_REDIRECT_URI ?? '';
const STATE_COOKIE = 'jarvez_spotify_oauth_state';
export const runtime = 'nodejs';

function resolveRedirectUri(request: Request): string {
  const configured = SPOTIFY_REDIRECT_URI.trim();
  if (configured) return configured;
  const origin = new URL(request.url).origin;
  return `${origin}/api/spotify/callback`;
}

function resolveTokenFilePath(): string {
  const configured = process.env.SPOTIFY_TOKENS_PATH?.trim();
  if (configured) {
    return path.isAbsolute(configured)
      ? configured
      : path.resolve(process.cwd(), '..', 'backend', configured);
  }
  return path.resolve(process.cwd(), '..', 'backend', 'data', 'spotify_tokens.json');
}

export async function GET(request: Request) {
  if (!SPOTIFY_CLIENT_ID || !SPOTIFY_CLIENT_SECRET) {
    return new NextResponse('Spotify credentials are not configured on frontend server', {
      status: 500,
    });
  }

  const url = new URL(request.url);
  const code = url.searchParams.get('code');
  const state = url.searchParams.get('state');
  const error = url.searchParams.get('error');
  if (error) {
    return new NextResponse(`Spotify authorization failed: ${error}`, { status: 400 });
  }
  if (!code) {
    return new NextResponse('Missing Spotify authorization code', { status: 400 });
  }

  const cookieHeader = request.headers.get('cookie') ?? '';
  const stateCookie = cookieHeader
    .split(';')
    .map((part) => part.trim())
    .find((part) => part.startsWith(`${STATE_COOKIE}=`))
    ?.split('=')
    .slice(1)
    .join('=');
  if (!stateCookie || !state || stateCookie !== state) {
    return new NextResponse('Invalid OAuth state', { status: 400 });
  }

  const redirectUri = resolveRedirectUri(request);
  const body = new URLSearchParams({
    grant_type: 'authorization_code',
    code,
    redirect_uri: redirectUri,
  });

  const basicAuth = Buffer.from(`${SPOTIFY_CLIENT_ID}:${SPOTIFY_CLIENT_SECRET}`).toString('base64');
  const tokenResponse = await fetch('https://accounts.spotify.com/api/token', {
    method: 'POST',
    headers: {
      Authorization: `Basic ${basicAuth}`,
      'Content-Type': 'application/x-www-form-urlencoded',
    },
    body,
  });
  const payload = await tokenResponse.json();
  if (!tokenResponse.ok || !payload?.access_token) {
    return new NextResponse(
      `Spotify token exchange failed: ${JSON.stringify(payload).slice(0, 500)}`,
      {
        status: 400,
      }
    );
  }

  const expiresIn = Number(payload.expires_in ?? 3600);
  const expiresAt = new Date(Date.now() + expiresIn * 1000).toISOString();
  const tokenFilePath = resolveTokenFilePath();
  await mkdir(path.dirname(tokenFilePath), { recursive: true });
  await writeFile(
    tokenFilePath,
    JSON.stringify(
      {
        access_token: String(payload.access_token),
        refresh_token: String(payload.refresh_token ?? ''),
        expires_at: expiresAt,
        updated_at: new Date().toISOString(),
      },
      null,
      2
    ),
    'utf-8'
  );

  const appUrl = process.env.NEXT_PUBLIC_APP_URL?.trim() || 'http://127.0.0.1:3001';
  const response = NextResponse.redirect(`${appUrl}/?spotify=connected`);
  response.cookies.delete(STATE_COOKIE);
  return response;
}
