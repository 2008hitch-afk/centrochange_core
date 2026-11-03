'use strict'
const { test } = require('node:test')
const assert = require('node:assert/strict')
const { classifyFailure, isPremiumPath, resolveTarget } = require('./audit10_failure_diagnostics.cjs')
test('redirect query is not the authenticated application pathname', () => {
  assert.equal(isPremiumPath(new URL('https://example.invalid/login?redirect-to=/premium')), false)
  assert.equal(isPremiumPath(new URL('https://example.invalid/premium#Agenda')), true)
})
test('targets are exact and cannot silently redirect the harness', () => {
  assert.equal(resolveTarget({}).mode, 'clone')
  assert.throws(() => resolveTarget({ CC_HARNESS_MODE: 'staging' }))
  assert.equal(resolveTarget({ CC_HARNESS_MODE: 'staging', CC_HARNESS_EXPECTED_SHA: 'a'.repeat(40) }).backend, 'centrochange-dev-backend-1')
  assert.throws(() => resolveTarget({ CC_HARNESS_MODE: 'staging', CC_HARNESS_EXPECTED_SHA: 'a'.repeat(40), CC_HARNESS_BASE: 'https://other.invalid' }))
  assert.throws(() => resolveTarget({ CC_HARNESS_MODE: 'production' }))
})
test('classifies diagnostics by observed evidence', () => {
  assert.equal(classifyFailure(new Error('locator timeout'), []), 'HARNESS_FAILURE')
  assert.equal(classifyFailure({ failureKind: 'AUTH_FAILURE' }, []), 'AUTH_FAILURE')
  assert.equal(classifyFailure(new Error(), [{ type: 'auth_denied', status: 403 }]), 'AUTH_FAILURE')
  assert.equal(classifyFailure(new Error(), [{ type: 'http', status: 500 }]), 'APP_FAILURE')
  assert.equal(classifyFailure(new Error(), [{ type: 'unexpected_status', status: 200 }]), 'APP_FAILURE')
})
