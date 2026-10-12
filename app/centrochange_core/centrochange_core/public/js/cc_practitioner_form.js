/* Native Healthcare form remains authoritative. These empty optional
   upstream fields are not part of the Centro Change client workflow. */
frappe.ui.form.on("Healthcare Practitioner", {
  refresh(frm) {
    const roles = new Set(frappe.user_roles || []);
    if (!roles.has("CC Manager") || frappe.session.user === "Administrator") return;
    const readable=String(frm.doc.practitioner_name||"").replace(/^CC-HTTP-UAT\d+\s+/,"");
    const label=({a:"Professionista Alfa",b:"Professionista Beta",c:"Professionista Gamma"})[readable]||readable;
    if(label) frm.page.set_title(label);
    if (!frm.doc.department) frm.toggle_display("department", false);
  },
});
