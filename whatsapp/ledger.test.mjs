import assert from 'node:assert/strict';
import { mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import test from 'node:test';
import { DeliveryLedger } from './ledger.mjs';

test('same delivery key sends once, including concurrent calls and restart', async () => {
  const dir = mkdtempSync(join(tmpdir(), 'kamartha-wa-'));
  try {
    const path = join(dir, 'ledger.json');
    let calls = 0;
    const deliver = async () => { calls++; return { id: 'synthetic-id', ack: 1 }; };
    const ledger = new DeliveryLedger(path);
    await Promise.all([ledger.send('key', '628111111111', 'dummy', deliver), ledger.send('key', '628111111111', 'dummy', deliver)]);
    assert.equal(calls, 1);
    assert.equal(ledger.receipt('key').state, 'SENT');
    const reopened = new DeliveryLedger(path);
    await reopened.send('key', '628111111111', 'dummy', deliver);
    assert.equal(calls, 1);
    await assert.rejects(() => reopened.send('key', '628111111111', 'changed', deliver), /KEY_CONFLICT/);
  } finally { rmSync(dir, { recursive: true }); }
});

test('lost or unacknowledged response remains unknown and is never blindly resent', async () => {
  const dir = mkdtempSync(join(tmpdir(), 'kamartha-wa-'));
  try {
    const ledger = new DeliveryLedger(join(dir, 'ledger.json'));
    let calls = 0;
    const deliver = async () => { calls++; throw new Error('lost'); };
    await ledger.send('key', '628111111111', 'dummy', deliver);
    await ledger.send('key', '628111111111', 'dummy', deliver);
    assert.equal(calls, 1);
    assert.equal(ledger.receipt('key').state, 'UNKNOWN');
    await ledger.send('pending', '628111111111', 'dummy', async () => ({ id: 'late', ack: 0 }));
    assert.equal(ledger.receipt('pending').state, 'UNKNOWN');
    assert.equal(ledger.acknowledge('pending', 'late').state, 'SENT');
    await ledger.send('after-submit', '628111111111', 'dummy', async (_number, _body, remember) => {
      remember('before-restart');
      throw new Error('lost while waiting for ack');
    });
    const reopened = new DeliveryLedger(join(dir, 'ledger.json'));
    assert.deepEqual(reopened.receipt('after-submit'), { state: 'UNKNOWN', message_id: 'before-restart' });
    assert.equal(reopened.acknowledge('after-submit', 'wrong-id').state, 'UNKNOWN');
    assert.equal(reopened.acknowledge('after-submit', 'before-restart').state, 'SENT');
  } finally { rmSync(dir, { recursive: true }); }
});
