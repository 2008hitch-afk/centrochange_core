// A 304 has no entity headers. Accept it only as a conditional cache validation.
function assetResponseError(response, kind) {
  const status = response.status();
  const mime = (response.headers()['content-type'] || '').split(';')[0];
  if (status === 304) {
    const headers = response.request().headers();
    return headers['if-none-match'] || headers['if-modified-since']
      ? null : {status, mime, reason:'UNCONDITIONAL_304'};
  }
  if (status >= 400 || (kind === 'css' && mime !== 'text/css') ||
      (kind === 'js' && !/javascript/.test(mime))) {
    return {status, mime, reason:'HTTP_OR_MIME'};
  }
  return null;
}
module.exports = {assetResponseError};
