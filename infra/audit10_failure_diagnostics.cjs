'use strict'
function classifyFailure(error, faults) {
  if (faults.some(x => x.status >= 500 || x.type === 'pageerror' || x.type === 'unexpected_status')) return 'APP_FAILURE'
  if (error.failureKind === 'AUTH_FAILURE' || faults.some(x => x.type === 'auth_denied')) return 'AUTH_FAILURE'
  return 'HARNESS_FAILURE'
}
function isPremiumPath(url) { return url.pathname === '/premium' }
function resolveTarget(env) {
  const mode = env.CC_HARNESS_MODE || 'clone'
  const targets = {
    clone: { base: 'http://centrochange.local:8099', backend: 'cc183-clone-backend' },
    staging: { base: 'https://centro-uat.empv.it', backend: 'centrochange-dev-backend-1' }
  }
  if (!targets[mode]) throw new Error('Unknown harness target')
  const target = targets[mode]
  if ((env.CC_HARNESS_BASE && env.CC_HARNESS_BASE !== target.base) || (env.CC_HARNESS_BACKEND && env.CC_HARNESS_BACKEND !== target.backend)) throw new Error('Harness target does not match approved environment')
  if (mode === 'staging' && !/^[0-9a-f]{40}$/.test(env.CC_HARNESS_EXPECTED_SHA || '')) throw new Error('Staging requires an explicit application SHA')
  return { mode, ...target, expectedSha: env.CC_HARNESS_EXPECTED_SHA || null }
}
module.exports = { classifyFailure, isPremiumPath, resolveTarget }
