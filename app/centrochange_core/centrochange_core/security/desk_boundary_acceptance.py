"""Read-only synthetic role check for native technical Desk surfaces.

Run on an isolated C109 site with the versioned UAT fixture. This does not
alter permissions or data. HTTP direct/API/export/print checks remain separate.
"""
import frappe


TECHNICAL_DOCTYPES = (
    "Builder Page", "Builder Workspace", "DocType", "Custom Field",
    "Client Script", "Server Script", "Role", "System Settings",
)


def run():
    from centrochange_core.uat.demo import credentials

    fixture = credentials()
    previous = frappe.session.user
    tested = {}
    try:
        for key in ("m", "s", "f", "t", "a", "b", "c"):
            user = fixture["users"][key]["name"]
            frappe.set_user(user)
            roles = set(frappe.get_roles(user))
            assert not roles.intersection({"System Manager", "Website Manager"}), (key, "technical role assigned")
            denied = []
            for doctype in TECHNICAL_DOCTYPES:
                if not frappe.db.exists("DocType", doctype):
                    continue
                # Frappe may expose role names/metadata for ordinary link
                # widgets. Creation and mutation of technical configuration
                # must still be denied; Builder itself must be unreadable.
                actions = ("read", "write", "create") if doctype.startswith("Builder ") else ("write", "create")
                for action in actions:
                    assert not frappe.has_permission(doctype, ptype=action, user=user), (key, doctype, action)
                denied.append(doctype)
            tested[key] = denied
        frappe.set_user("Administrator")
        assert frappe.has_permission("DocType", ptype="read", user="Administrator")
        return {"status": "PASS", "clients": tested, "hitch_administrator": "SEPARATE", "mutations": "NONE"}
    finally:
        frappe.set_user(previous)
