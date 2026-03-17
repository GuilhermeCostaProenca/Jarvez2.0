import { existsSync, rmSync } from 'node:fs';
import path from 'node:path';

const nextDir = path.join(process.cwd(), '.next');

if (existsSync(nextDir)) {
  try {
    rmSync(nextDir, { recursive: true, force: true, maxRetries: 3 });
  } catch (error) {
    console.warn(`Failed to clean .next directory: ${String(error)}`);
  }
}
