const assert=require('node:assert/strict');
const {assetResponseError}=require('./issue139_asset_response.cjs');
function response(status,mime,headers={}) {return {status:()=>status,headers:()=>({'content-type':mime}),request:()=>({headers:()=>headers})};}
assert.equal(assetResponseError(response(200,'text/css'),'css'),null);
assert.equal(assetResponseError(response(200,'application/javascript'),'js'),null);
assert.equal(assetResponseError(response(304,'',{'if-none-match':'"abc"'}),'css'),null);
assert.equal(assetResponseError(response(304,'',{'if-modified-since':'Mon, 01 Jan 2024 00:00:00 GMT'}),'js'),null);
assert.equal(assetResponseError(response(304,''),'css').reason,'UNCONDITIONAL_304');
assert.equal(assetResponseError(response(404,'text/html'),'css').reason,'HTTP_OR_MIME');
assert.equal(assetResponseError(response(200,'text/html'),'css').reason,'HTTP_OR_MIME');
assert.equal(assetResponseError(response(200,'text/css'),'js').reason,'HTTP_OR_MIME');
console.log('asset response classification PASS');
