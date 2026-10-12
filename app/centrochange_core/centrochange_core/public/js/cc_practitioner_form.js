/* Native Healthcare form remains authoritative. These empty optional
   upstream fields are not part of the Centro Change client workflow. */
frappe.ui.form.on("Healthcare Practitioner", {
  refresh(frm) {
    const roles = new Set(frappe.user_roles || []);
    if (!roles.has("CC Manager") || frappe.session.user === "Administrator") return;
    if (!frm.doc.department) frm.toggle_display("department", false);
  },
});
