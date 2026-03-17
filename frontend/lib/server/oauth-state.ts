type StateRecord = {
  provider: string;
  expiresAt: number;
};

const STATE_TTL_MS = 10 * 60 * 1000;

function getStore(): Map<string, StateRecord> {
  const globalScope = globalThis as typeof globalThis & {
    __jarvezOauthStates?: Map<string, StateRecord>;
  };
  if (!globalScope.__jarvezOauthStates) {
    globalScope.__jarvezOauthStates = new Map<string, StateRecord>();
  }
  return globalScope.__jarvezOauthStates;
}

function pruneExpiredStates(store: Map<string, StateRecord>, now: number) {
  for (const [key, record] of store.entries()) {
    if (record.expiresAt <= now) {
      store.delete(key);
    }
  }
}

export function registerOauthState(provider: string, state: string) {
  const now = Date.now();
  const store = getStore();
  pruneExpiredStates(store, now);
  store.set(state, {
    provider,
    expiresAt: now + STATE_TTL_MS,
  });
}

export function consumeOauthState(provider: string, state: string): boolean {
  const now = Date.now();
  const store = getStore();
  pruneExpiredStates(store, now);
  const record = store.get(state);
  if (!record || record.provider !== provider) {
    return false;
  }
  store.delete(state);
  return true;
}
