from centrochange_core.security.guards import require_manager
no_cache = True


def get_context(context):
    require_manager()
    context.title = 'Centro Change — Registro modifiche'
