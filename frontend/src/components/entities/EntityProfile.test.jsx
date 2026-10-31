import test from 'node:test';
import assert from 'node:assert/strict';
import { maskEmail, maskNationalId } from './EntityProfile.jsx';

test('compliance officers see the full national id and email', () => {
  assert.equal(maskNationalId('0012345678', ['COMPLIANCE_OFFICER']), '0012345678');
  assert.equal(maskEmail('ali@example.ir', ['COMPLIANCE_OFFICER']), 'ali@example.ir');
});

test('other roles see partial national id and email', () => {
  assert.equal(maskNationalId('0012345678', ['INVESTIGATOR']), '001••••678');
  assert.equal(maskEmail('ali@example.ir', ['SUPERVISOR']), 'a•••@example.ir');
});

test('masking keeps missing values explicit', () => {
  assert.equal(maskNationalId('', ['INVESTIGATOR']), '—');
  assert.equal(maskEmail(null, ['INVESTIGATOR']), '—');
  assert.equal(maskEmail('not-an-email', ['INVESTIGATOR']), '•••');
});
