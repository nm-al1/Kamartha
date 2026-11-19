import { createHash } from 'node:crypto';
import { existsSync, readFileSync, renameSync, writeFileSync } from 'node:fs';

export class DeliveryLedger {
  constructor(path) {
    this.path = path;
    this.rows = existsSync(path) ? JSON.parse(readFileSync(path, 'utf8')) : {};
    for (const value of Object.values(this.rows)) {
      if (value.state === 'SENDING') value.state = 'UNKNOWN';
    }
    this.persist();
  }

  persist() {
    writeFileSync(`${this.path}.tmp`, JSON.stringify(this.rows), { mode: 0o600 });
    renameSync(`${this.path}.tmp`, this.path);
  }

  receipt(key) {
    const row = this.rows[key];
    return row ? { state: row.state, message_id: row.message_id ?? null } : { state: 'NOT_FOUND' };
  }

  acknowledge(key, messageId) {
    const row = this.rows[key];
    if (row && row.message_id === messageId) {
      row.state = 'SENT';
      this.persist();
    }
    return this.receipt(key);
  }

  async send(key, number, message, deliver) {
    const hash = createHash('sha256').update(JSON.stringify([number, message])).digest('hex');
    const previous = this.rows[key];
    if (previous) {
      if (previous.hash !== hash) throw new Error('KEY_CONFLICT');
      return this.receipt(key);
    }
    if (Object.keys(this.rows).length >= 10000) throw new Error('LEDGER_FULL');
    this.rows[key] = { hash, state: 'SENDING' };
    this.persist();
    try {
      const result = await deliver(number, message, id => {
        this.rows[key].message_id = id;
        this.persist();
      });
      this.rows[key] = { hash, state: result.ack >= 1 && result.id ? 'SENT' : 'UNKNOWN', message_id: result.id ?? null };
    } catch {
      this.rows[key].state = 'UNKNOWN';
    }
    this.persist();
    return this.receipt(key);
  }
}
