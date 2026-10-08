"""Never retain authenticated financial/identity responses across browser account switches."""


def protect(request, response):
    if response is None:
        return
    path=request.path
    if path.startswith(('/api/','/private/files/')) or path in ('/centrochange','/finanza','/professionista','/pazienti_report','/registro_modifiche','/validazione','/printview'):
        # Preserve all native authorization decisions/statuses; only prevent cache replay.
        response.headers['Cache-Control']='private, no-store, no-cache, max-age=0, must-revalidate'
        response.headers['Pragma']='no-cache'
        response.headers['Expires']='0'
