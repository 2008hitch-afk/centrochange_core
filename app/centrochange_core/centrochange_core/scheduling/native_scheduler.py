"""Prevent Healthcare's native daily job from bypassing Centro Change lifecycle.

Healthcare's update_appointment_status() loops Patient Appointment documents and
calls .save(). That changes native statuses (including No Show) outside the CC
audited lifecycle, and is correctly denied by AppointmentMixin.validate.
Frappe 16 keeps the 'stopped' bit across Scheduled Job Type sync. This
configuration is explicitly reapplied *after* sync_jobs during migrations.
No bypass of AppointmentMixin, no patient/appointment mutations.
"""

UPSTREAM_JOB = (
    "healthcare.healthcare.doctype.patient_appointment."
    "patient_appointment.update_appointment_status"
)
OWN_CATCH_UP = "centrochange_core.operations.automation.catch_up"


def inspect():
    """Observe the scheduler entries only; safe for live read-only checks."""
    import frappe

    rows = frappe.get_all(
        "Scheduled Job Type",
        filters={"method": UPSTREAM_JOB},
        fields=["name", "method", "stopped"],
        page_length=3,
    )
    active = frappe.get_all(
        "Scheduled Job Type",
        filters={"method": OWN_CATCH_UP},
        fields=["name", "method", "stopped"],
        page_length=3,
    )
    return {
        "native_count": len(rows),
        "native_stopped": len(rows) == 1 and bool(rows[0].stopped),
        "cc_catch_up_count": len(active),
        "cc_catch_up_active": len(active) == 1 and not bool(active[0].stopped),
    }


def configure():
    """After Frappe sync_jobs: disable only the conflicting native job."""
    import frappe

    if not {"healthcare", "centrochange_core"} <= set(frappe.get_installed_apps()):
        frappe.throw("Centro Change scheduler requires installed Healthcare and Centro Change.")
    scheduler_events = frappe.get_hooks("scheduler_events") or {}
    cron = scheduler_events.get("cron") or {}
    if OWN_CATCH_UP not in (cron.get("*/5 * * * *") or []):
        frappe.throw("Centro Change catch-up scheduler hook not registered: cannot disable Healthcare job.")

    state = inspect()
    if state["native_count"] != 1 or state["cc_catch_up_count"] != 1:
        frappe.throw("Scheduled Job Type registrations inconsistent: do not change native scheduler.")
    if not state["cc_catch_up_active"]:
        frappe.throw("Centro Change catch-up job is stopped; enable it before disabling Healthcare job.")

    if not state["native_stopped"]:
        name = frappe.db.get_value("Scheduled Job Type", {"method": UPSTREAM_JOB}, "name")
        frappe.db.set_value("Scheduled Job Type", name, "stopped", 1)
        state = inspect()
    if not state["native_stopped"]:
        frappe.throw("Healthcare daily appointment job was not stopped: migration cannot complete.")
    return state
