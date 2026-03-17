import { NextResponse } from 'next/server';
import { AccessToken, type AccessTokenOptions, type VideoGrant } from 'livekit-server-sdk';
import { RoomConfiguration } from '@livekit/protocol';

type ConnectionDetails = {
  serverUrl: string;
  roomName: string;
  participantName: string;
  participantToken: string;
  participantIdentity: string;
};

type RateLimitEntry = {
  count: number;
  windowStart: number;
};

const API_KEY = process.env.LIVEKIT_API_KEY;
const API_SECRET = process.env.LIVEKIT_API_SECRET;
const LIVEKIT_URL = process.env.LIVEKIT_URL;
const TOKEN_ALLOWED_ORIGINS = (process.env.TOKEN_ALLOWED_ORIGINS ?? '')
  .split(',')
  .map((item) => item.trim())
  .filter(Boolean);

const ROOM_NAME_REGEX = /^[a-zA-Z0-9_-]{3,64}$/;
const PARTICIPANT_IDENTITY_REGEX = /^[a-zA-Z0-9_-]{3,64}$/;
const RATE_LIMIT_WINDOW_MS = 60_000;
const RATE_LIMIT_MAX_REQUESTS = 30;
const IDENTITY_COOKIE_NAME = 'jarvez_participant_identity';

const globalRateLimitStore =
  (globalThis as { __jarvezRateLimitStore?: Map<string, RateLimitEntry> }).__jarvezRateLimitStore ??
  new Map<string, RateLimitEntry>();
(globalThis as { __jarvezRateLimitStore?: Map<string, RateLimitEntry> }).__jarvezRateLimitStore =
  globalRateLimitStore;

export const revalidate = 0;

export async function POST(req: Request) {
  try {
    if (!LIVEKIT_URL) throw new Error('LIVEKIT_URL is not defined');
    if (!API_KEY) throw new Error('LIVEKIT_API_KEY is not defined');
    if (!API_SECRET) throw new Error('LIVEKIT_API_SECRET is not defined');

    const origin = req.headers.get('origin');
    if (!isAllowedOrigin(origin)) {
      return new NextResponse('Origin not allowed', { status: 403 });
    }

    const requestKey = buildRateLimitKey(req);
    if (!checkRateLimit(requestKey)) {
      return new NextResponse('Too many requests', { status: 429 });
    }

    const body = await req.json();
    const agentName: string | undefined = body?.room_config?.agents?.[0]?.agent_name;
    const requestedRoomName: string | undefined = body?.room_name;
    const requestedIdentity: string | undefined = body?.participant_identity;

    const participantName = 'user';
    const participantIdentity = resolveParticipantIdentity(req, requestedIdentity);
    const generatedRoomName = `voice_assistant_room_${Math.floor(Math.random() * 1_000_000)}`;
    const roomName = requestedRoomName ?? generatedRoomName;

    if (!ROOM_NAME_REGEX.test(roomName)) {
      return new NextResponse('Invalid room name', { status: 400 });
    }

    const participantToken = await createParticipantToken(
      { identity: participantIdentity, name: participantName },
      roomName,
      agentName
    );

    const data: ConnectionDetails = {
      serverUrl: LIVEKIT_URL,
      roomName,
      participantToken,
      participantName,
      participantIdentity,
    };

    return NextResponse.json(data, {
      headers: {
        'Cache-Control': 'no-store',
        'Set-Cookie': `${IDENTITY_COOKIE_NAME}=${participantIdentity}; Path=/; Max-Age=31536000; SameSite=Lax`,
      },
    });
  } catch (error) {
    if (error instanceof Error) {
      console.error(error);
      return new NextResponse(error.message, { status: 500 });
    }
    return new NextResponse('Unknown server error', { status: 500 });
  }
}

function resolveParticipantIdentity(req: Request, requestedIdentity?: string): string {
  const requested = requestedIdentity?.trim();
  if (requested && PARTICIPANT_IDENTITY_REGEX.test(requested)) {
    return requested;
  }

  const cookieHeader = req.headers.get('cookie') ?? '';
  const cookieMatch = cookieHeader
    .split(';')
    .map((item) => item.trim())
    .find((item) => item.startsWith(`${IDENTITY_COOKIE_NAME}=`));
  if (cookieMatch) {
    const cookieValue = decodeURIComponent(cookieMatch.split('=').slice(1).join('=')).trim();
    if (PARTICIPANT_IDENTITY_REGEX.test(cookieValue)) {
      return cookieValue;
    }
  }

  return `voice_assistant_user_${Math.floor(Math.random() * 1_000_000)}`;
}

function isAllowedOrigin(origin: string | null): boolean {
  if (!origin) return true;

  try {
    const parsedOrigin = new URL(origin);
    const isLocalhost =
      (parsedOrigin.protocol === 'http:' || parsedOrigin.protocol === 'https:') &&
      (parsedOrigin.hostname === 'localhost' || parsedOrigin.hostname === '127.0.0.1');

    if (isLocalhost) {
      return true;
    }
  } catch {
    return false;
  }

  return TOKEN_ALLOWED_ORIGINS.includes(origin);
}

function buildRateLimitKey(req: Request): string {
  const forwardedFor = req.headers.get('x-forwarded-for');
  if (forwardedFor) {
    const first = forwardedFor.split(',')[0]?.trim();
    if (first) return first;
  }

  return req.headers.get('origin') ?? 'unknown-client';
}

function checkRateLimit(key: string): boolean {
  const now = Date.now();
  const entry = globalRateLimitStore.get(key);

  if (!entry || now - entry.windowStart >= RATE_LIMIT_WINDOW_MS) {
    globalRateLimitStore.set(key, { count: 1, windowStart: now });
    return true;
  }

  if (entry.count >= RATE_LIMIT_MAX_REQUESTS) {
    return false;
  }

  entry.count += 1;
  globalRateLimitStore.set(key, entry);
  return true;
}

function createParticipantToken(
  userInfo: AccessTokenOptions,
  roomName: string,
  agentName?: string
): Promise<string> {
  const at = new AccessToken(API_KEY, API_SECRET, {
    ...userInfo,
    ttl: '3m',
  });

  const grant: VideoGrant = {
    room: roomName,
    roomJoin: true,
    canPublish: true,
    canPublishData: true,
    canSubscribe: true,
  };
  at.addGrant(grant);

  if (agentName) {
    at.roomConfig = new RoomConfiguration({
      agents: [{ agentName }],
    });
  }

  return at.toJwt();
}
