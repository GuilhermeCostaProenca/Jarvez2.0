import { NextResponse } from 'next/server';
import { createHmac, timingSafeEqual } from 'crypto';
import { mkdir, readFile, writeFile } from 'fs/promises';
import path from 'path';

export const runtime = 'nodejs';

function resolveInboxPath(): string {
  const configured = process.env.WHATSAPP_INBOX_PATH?.trim();
  if (configured) {
    return path.isAbsolute(configured)
      ? configured
      : path.resolve(process.cwd(), '..', 'backend', configured);
  }
  return path.resolve(process.cwd(), '..', 'backend', 'data', 'whatsapp_inbox.json');
}

async function loadInbox(): Promise<Record<string, unknown>[]> {
  const filePath = resolveInboxPath();
  try {
    const raw = await readFile(filePath, 'utf-8');
    const parsed = JSON.parse(raw);
    if (Array.isArray(parsed)) {
      return parsed.filter((item) => typeof item === 'object' && item !== null) as Record<
        string,
        unknown
      >[];
    }
  } catch {
    return [];
  }
  return [];
}

async function saveInbox(items: Record<string, unknown>[]): Promise<void> {
  const filePath = resolveInboxPath();
  await mkdir(path.dirname(filePath), { recursive: true });
  await writeFile(filePath, JSON.stringify(items, null, 2), 'utf-8');
}

function verifySignature(rawBody: string, signatureHeader: string | null): boolean {
  const appSecret = process.env.WHATSAPP_APP_SECRET?.trim();
  if (!appSecret) return true;
  if (!signatureHeader || !signatureHeader.startsWith('sha256=')) return false;

  const expected = createHmac('sha256', appSecret).update(rawBody, 'utf8').digest('hex');
  const actual = signatureHeader.replace('sha256=', '');
  try {
    return timingSafeEqual(Buffer.from(expected), Buffer.from(actual));
  } catch {
    return false;
  }
}

export async function GET(request: Request) {
  const url = new URL(request.url);
  const mode = url.searchParams.get('hub.mode');
  const token = url.searchParams.get('hub.verify_token');
  const challenge = url.searchParams.get('hub.challenge');
  const expectedToken = process.env.WHATSAPP_VERIFY_TOKEN?.trim();

  if (mode === 'subscribe' && token && expectedToken && token === expectedToken && challenge) {
    return new NextResponse(challenge, { status: 200 });
  }
  return new NextResponse('Forbidden', { status: 403 });
}

export async function POST(request: Request) {
  const rawBody = await request.text();
  const signature = request.headers.get('x-hub-signature-256');
  if (!verifySignature(rawBody, signature)) {
    return new NextResponse('Invalid signature', { status: 401 });
  }

  let payload: Record<string, unknown> | null = null;
  try {
    payload = JSON.parse(rawBody) as Record<string, unknown>;
  } catch {
    return new NextResponse('Invalid JSON', { status: 400 });
  }

  const entries = (payload?.entry as Record<string, unknown>[] | undefined) ?? [];
  const stored = await loadInbox();
  const normalized: Record<string, unknown>[] = [];

  for (const entry of entries) {
    const changes = (entry?.changes as Record<string, unknown>[] | undefined) ?? [];
    for (const change of changes) {
      const value = change?.value as Record<string, unknown> | undefined;
      const messages = (value?.messages as Record<string, unknown>[] | undefined) ?? [];
      const contacts = (value?.contacts as Record<string, unknown>[] | undefined) ?? [];
      const contact = contacts[0];
      const waId = String(contact?.wa_id ?? '');
      const profileName = String(
        (contact?.profile as Record<string, unknown> | undefined)?.name ?? ''
      );

      for (const message of messages) {
        const type = String(message?.type ?? '');
        const text = String((message?.text as Record<string, unknown> | undefined)?.body ?? '');
        normalized.push({
          id: String(message?.id ?? ''),
          from: String(message?.from ?? waId),
          profile_name: profileName,
          type,
          text,
          timestamp: String(message?.timestamp ?? Date.now()),
          received_at: new Date().toISOString(),
          raw: message,
        });
      }
    }
  }

  if (normalized.length > 0) {
    const merged = [...normalized, ...stored].slice(0, 200);
    await saveInbox(merged);
  }

  return NextResponse.json({ received: true });
}
