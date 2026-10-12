/* Supported native Form Script: human title, canonical fields unchanged. */
frappe.ui.form.on("Patient", {
  refresh(frm) {
    if (frappe.session.user === "Administrator" || !(frappe.user_roles || []).some(role => role.startsWith("CC "))) return;
    const label=String(frm.doc.patient_name||"").replace(/^CC-HTTP-UAT\d+\s+/,"");
    if(label) frm.page.set_title(label);
  },
});
