/* Supported native List View settings; no change to Patient permissions. */
if (frappe.session.user !== "Administrator" && (frappe.user_roles || []).some(role => role.startsWith("CC "))) {
const ccPatientList = frappe.listview_settings["Patient"] || {};
frappe.listview_settings["Patient"] = {
  ...ccPatientList,
  hide_name_column: true,
  hide_name_filter: true,
  onload(listview) {
    ccPatientList.onload?.(listview);
    listview.page.set_title("Pazienti");
  },
  formatters: {
    ...(ccPatientList.formatters || {}),
    patient_name(value) {
      const label = String(value || "").replace(/^CC-HTTP-UAT\d+\s+/, "");
      return frappe.utils.escape_html(label);
    },
  },
};
}
