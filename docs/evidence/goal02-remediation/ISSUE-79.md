# #79 — Searchable operational selectors

Static checks PASS; integrated runtime/browser check pending. Branch `issue-79/searchable-selectors`, base `issue-74/authorized-patient-search`.
Existing canonical native select values retained, with searchable authorized display labels. Patient booking searches bounded existing server-authorized Patient query; professional assignment/booking and professional report search authorized bootstrap data. Agenda popup filters its existing authorized checkboxes. No new role, visibility, schema or mutation in browser acceptance. Async generation cancellation prevents older selector replies overwriting current input/context. Owner final UI review required.
