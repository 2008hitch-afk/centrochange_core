"""Client landing on the one approved UI; native Desk remains technical."""

import frappe


OPERATING_ROLES = {"CC Manager", "CC Secretariat", "CC Professional"}
FINANCE_ROLES = {"CC Finance", "CC Accountant"}
CLIENT_ROLES = OPERATING_ROLES | FINANCE_ROLES
LEGACY_WEB = {"/centrochange", "/finanza", "/professionista", "/pazienti_report",
              "/registro_modifiche", "/validazione"}


def premium_primary():
    # Site-local switch. Keep false until live integration and Owner visual UAT pass.
    return frappe.utils.cint(frappe.conf.get("cc_premium_primary")) == 1


def client_home(user=None):
    user = user or frappe.session.user
    if user in ("Guest", "Administrator"):
        return None
    roles = set(frappe.get_roles(user))
    if premium_primary() and roles & CLIENT_ROLES:
        return "/premium"
    if roles & OPERATING_ROLES:
        return "/app/cc-unified-desk?cc_view=agenda"
    if roles & FINANCE_ROLES:
        return "/app/cc-unified-desk?cc_view=finance"
    return None


def app_visible():
    return client_home() is not None


def configure_user(doc, method=None):
    if doc.name in ("Guest", "Administrator") or doc.user_type != "System User":
        return
    assigned = {row.role for row in doc.get("roles", [])}
    if assigned & CLIENT_ROLES and doc.default_app != "centrochange_core":
        # This is a native Frappe User preference. db.set_value avoids the
        # User on_update lifecycle repeating itself.
        frappe.db.set_value("User", doc.name, "default_app", "centrochange_core", update_modified=False)
    elif not assigned & CLIENT_ROLES and doc.default_app == "centrochange_core":
        frappe.db.set_value("User", doc.name, "default_app", "", update_modified=False)


def configure_existing_users():
    for name in frappe.get_all("User", filters={"enabled": 1, "user_type": "System User"}, pluck="name"):
        if name != "Administrator" and client_home(name):
            if frappe.db.get_value("User", name, "default_app") != "centrochange_core":
                frappe.db.set_value("User", name, "default_app", "centrochange_core", update_modified=False)


def redirect_launcher(response, request):
    """Redirect only exact launcher URLs; preserve valid document deep links."""
    if response is None or response.status_code >= 400:
        return
    if request.method not in ("GET", "HEAD") or request.path not in ("/", "/app", "/desk"):
        return
    target = client_home()
    if not target:
        return
    response.status_code = 302
    response.headers["Location"] = target
    response.headers["Cache-Control"] = "private, no-store"
    response.set_data(b"")


def redirect_legacy_operational_routes(response, request):
    """Redirect legacy web responses after Frappe has authenticated the request.

    A before_request hook cannot raise frappe.Redirect: Frappe's app catches it
    as an error page, which leaves deep Desk URLs visible to client roles.
    """
    if not premium_primary():
        return
    if response is None or response.status_code >= 400:
        return
    if not request or request.method not in ("GET", "HEAD"):
        return
    path = request.path.rstrip("/") or "/"
    if path == "/primo_incontro":
        target = "/premium-primo-incontro"
    else:
        user = frappe.session.user
        roles = set(frappe.get_roles(user)) if user not in ("Guest", "Administrator") else set()
        if not roles & CLIENT_ROLES:
            return
        if path not in LEGACY_WEB and not any(
            path == prefix or path.startswith(prefix + "/")
            for prefix in ("/app", "/desk")
        ):
            return
        target = "/premium"
    response.status_code = 302
    response.headers["Location"] = target
    response.headers["Cache-Control"] = "private, no-store"
    response.set_data(b"")
