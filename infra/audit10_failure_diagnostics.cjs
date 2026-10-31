'use strict'
function classifyFailure(error, faults) {
  if (faults.some(x => x.status >= 500 || x.type === 'pageerror' || x.type === 'unexpected_status')) return 'APP_FAILURE'
  if (error.failureKind === 'AUTH_FAILURE' || faults.some(x => x.type === 'auth_denied')) return 'AUTH_FAILURE'
  return 'HARNESS_FAILURE'
}
function isPremiumPath(url) { return url.pathname === '/premium' }
module.exports = { classifyFailure, isPremiumPath }
