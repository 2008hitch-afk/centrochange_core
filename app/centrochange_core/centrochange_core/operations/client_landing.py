"""Client landing on the existing Frappe Desk, without changing permissions."""

import frappe


OPERATING_ROLES = {"CC Manager", "CC Secretariat", "CC Professional"}
FINANCE_ROLES = {"CC Finance", "CC Accountant"}
CLIENT_ROLES = OPERATING_ROLES | FINANCE_ROLES


def client_home(user=None):
    user = user or frappe.session.user
    if user in ("Guest", "Administrator"):
        return None
    roles = set(frappe.get_roles(user))
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
    if request.method not in ("GET", "HEAD") or request.path not in ("/", "/app", "/desk"):
        return
    target = client_home()
    if not target:
        return
    response.status_code = 302
    response.headers["Location"] = target
    response.headers["Cache-Control"] = "private, no-store"
    response.set_data(b"")
