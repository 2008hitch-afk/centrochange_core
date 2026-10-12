/* Supported native List View settings; no change to Patient permissions. */
frappe.listview_settings["Patient"] = {
  ...(frappe.listview_settings["Patient"] || {}),
  hide_name_column: true,
  hide_name_filter: true,
  formatters: {
    ...(frappe.listview_settings["Patient"]?.formatters || {}),
    patient_name(value) {
      const label = String(value || "").replace(/^CC-HTTP-UAT\d+\s+/, "");
      return frappe.utils.escape_html(label);
    },
  },
};
