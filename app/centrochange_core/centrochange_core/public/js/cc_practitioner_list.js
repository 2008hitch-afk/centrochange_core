/* The department Link is removed from standard filters by the versioned
   Property Setter. No Medical Department permission is granted here. */
frappe.listview_settings["Healthcare Practitioner"] = {
  ...(frappe.listview_settings["Healthcare Practitioner"] || {}),
  hide_name_column: true,
  hide_name_filter: true,
  formatters: {
    ...(frappe.listview_settings["Healthcare Practitioner"]?.formatters || {}),
    practitioner_name(value) {
      const label = String(value || "").replace(/^CC-HTTP-UAT\d+\s+/, "");
      return frappe.utils.escape_html(label);
    },
  },
};
