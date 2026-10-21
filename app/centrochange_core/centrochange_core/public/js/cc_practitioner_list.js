/* The department Link is removed from standard filters by the versioned
   Property Setter. No Medical Department permission is granted here. */
if (frappe.session.user !== "Administrator" && (frappe.user_roles || []).some(role => role.startsWith("CC "))) {
const ccPractitionerList = frappe.listview_settings["Healthcare Practitioner"] || {};
frappe.listview_settings["Healthcare Practitioner"] = {
  ...ccPractitionerList,
  hide_name_column: true,
  hide_name_filter: true,
  onload(listview) {
    ccPractitionerList.onload?.(listview);
    listview.page.set_title("Professionisti");
  },
  formatters: {
    ...(ccPractitionerList.formatters || {}),
    practitioner_name(value) {
      const raw=String(value || "").replace(/^CC-HTTP-UAT\d+\s+/, "");
      const label=({a:"Professionista Alfa",b:"Professionista Beta",c:"Professionista Gamma"})[raw]||raw;
      return frappe.utils.escape_html(label);
    },
  },
};
}
