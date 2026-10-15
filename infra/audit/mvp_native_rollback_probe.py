"""Append to the common audit preamble; test native masters using only new rows."""
from uuid import uuid4
tag = "CC AUDIT " + uuid4().hex[:10]
results = []
created = {}
try:
    for doctype in ("Patient", "Healthcare Practitioner", "Item", "Item Price", "Appointment Type", "CC Center Service", "CC Package Template"):
        frappe.set_user("Administrator")
        try:
            source = frappe.get_all(doctype, fields=["name"], limit_page_length=1)
            assert source, "No approved synthetic native source"
            doc = frappe.copy_doc(frappe.get_doc(doctype, source[0].name))
            doc.name = None
            if doctype == "Patient":
                doc.first_name = tag; doc.last_name = "SYNTHETIC"; doc.uid = tag
                doc.email = "cc-audit@example.invalid"; doc.user_id = None; doc.customer = None
                doc.cc_intake_key = None; doc.cc_intake_hash = None
                field, value = "first_name", tag + " UPDATED"
            elif doctype == "Healthcare Practitioner":
                doc.first_name = tag; doc.last_name = "SYNTHETIC"; doc.practitioner_name = tag; doc.user_id = None; doc.supplier = None
                field, value = "first_name", tag + " UPDATED"
            elif doctype == "Item":
                doc.item_code = tag; doc.item_name = tag; doc.is_stock_item = 0
                field, value = "item_name", tag + " UPDATED"
            elif doctype == "Item Price":
                assert created.get("Item")
                doc.item_code = created["Item"]; doc.price_list_rate = 123
                field, value = "price_list_rate", 124
            elif doctype == "Appointment Type":
                doc.name = tag; doc.appointment_type = tag
                field, value = "default_duration", 45
            elif doctype == "CC Center Service":
                assert created.get("Appointment Type")
                doc.appointment_type = created["Appointment Type"]
                field, value = "enabled", 0
            else:
                doc.title = tag
                field, value = "title", tag + " UPDATED"
            existing_names = set(frappe.get_all(doctype, pluck="name", limit_page_length=0))
            doc.insert()
            assert doc.name not in existing_names, "Native insert reused a preexisting identity"
            created[doctype] = doc.name
            assert doc.meta.has_field(field), field
            doc.set(field, value); doc.save(); doc.reload()
            assert doc.get(field) == value, (doctype, field)
            results.append({"doctype": doctype, "status": "PASS", "role": "Administrator", "checks": ["native insert", "native save", "reload exact value"], "record": doc.name})
        except Exception as error:
            results.append({"doctype": doctype, "status": "BLOCKED", "error_type": type(error).__name__, "error": str(error)})
    print("AUDIT_NATIVE=" + json.dumps(results, default=str), flush=True)
finally:
    frappe.db.rollback()
    after = fingerprint()
    print("AUDIT_NATIVE_INTEGRITY=" + json.dumps({"unchanged": before == after, "changed_tables": [k for k in before if before[k] != after.get(k)]}), flush=True)
    frappe.destroy()
