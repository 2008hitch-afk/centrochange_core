"""Read-only native accounting reports exposed through a strict center scope.

Generic ERPNext Query Report endpoints remain blocked for client roles. These
two projections pin company, operational cost center and date range server-side.
"""
import csv
import re
from datetime import date, datetime
from io import StringIO

import frappe

from centrochange_core.finance.guards import require_finance
from centrochange_core.finance.reporting import _interval
from centrochange_core.security.guards import operational_centers, current_rows
from centrochange_core.operations.reporting import safe_cell


REPORTS = {"general_ledger", "trial_balance"}
MAX_ROWS = 2000


def _scope(center, start, end):
    require_finance(center)
    start, end = _interval(start, end)
    if (end - start).days > 366:
        frappe.throw("Seleziona un periodo contabile non superiore a 366 giorni.")
    branches = current_rows(
        "Branch", {"name": center}, fields=["name", "cc_company", "cc_cost_center"]
    )
    if not branches or not any(row.name == center for row in operational_centers()):
        frappe.throw("La sede non è attiva per i report contabili.", frappe.PermissionError)
    branch = branches[0]
    if not branch.cc_company or not branch.cc_cost_center:
        frappe.throw("La sede non ha una società e un centro di costo configurati.")
    cost_center = frappe.db.get_value(
        "Cost Center", branch.cc_cost_center, ["company", "is_group", "disabled"], as_dict=True
    )
    if not cost_center or cost_center.company != branch.cc_company or cost_center.is_group or cost_center.disabled:
        frappe.throw("Il centro di costo configurato non è utilizzabile.", frappe.PermissionError)
    return branch, start, end


def _filters(report, branch, start, end):
    filters = frappe._dict({
        "company": branch.cc_company,
        "from_date": start,
        "to_date": end,
        "cost_center": frappe.as_json([branch.cc_cost_center]),
    })
    if report == "trial_balance":
        years = frappe.get_all(
            "Fiscal Year",
            filters={"company": branch.cc_company, "disabled": 0,
                     "year_start_date": ["<=", start], "year_end_date": [">=", end]},
            pluck="name", limit=2,
        )
        if len(years) != 1:
            frappe.throw("Il periodo del bilancio di verifica deve rientrare in un solo esercizio configurato.")
        filters.fiscal_year = years[0]
    return filters


def _run(report, branch, start, end):
    if report == "general_ledger":
        from erpnext.accounts.report.general_ledger.general_ledger import execute
    elif report == "trial_balance":
        from erpnext.accounts.report.trial_balance.trial_balance import execute
    else:
        frappe.throw("Report contabile non disponibile.")
    columns, rows = execute(_filters(report, branch, start, end))
    if len(rows) > MAX_ROWS:
        frappe.throw("Riduci il periodo del report: i risultati superano il limite consentito.")
    from frappe.desk.query_report import get_column_as_dict
    columns=[get_column_as_dict(column) for column in columns]
    labels = [frappe._(column.get("label") or column.get("fieldname") or "Dato") for column in columns]
    normalized = []
    for row in rows:
        if isinstance(row, dict):
            normalized.append([row.get(column.get("fieldname")) for column in columns])
        elif isinstance(row, (tuple, list)):
            normalized.append(list(row))
        else:
            normalized.append([row])
    return labels, normalized


@frappe.whitelist(methods=["GET"])
def run(center, report, start, end):
    if report not in REPORTS:
        frappe.throw("Seleziona un report contabile supportato.")
    branch, start, end = _scope(center, start, end)
    labels, rows = _run(report, branch, start, end)
    return {"report": report, "center": center, "company": branch.cc_company,
            "start": start, "end": end, "columns": labels, "rows": rows,
            "read_only": True}


@frappe.whitelist(methods=["GET"])
def export_csv(center, report, start, end):
    data = run(center, report, start, end)
    output = StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow(data["columns"])
    for row in data["rows"]:
        values=[]
        for value in row:
            if isinstance(value, (date, datetime)) or isinstance(value,str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}",value):
                value=frappe.utils.formatdate(value,'dd/MM/yyyy')
            values.append(safe_cell(value))
        writer.writerow(values)
    title = "libro-giornale" if report == "general_ledger" else "bilancio-verifica"
    frappe.response.update({"type": "download", "filename": f"{title}.csv",
        "filecontent": output.getvalue(), "content_type": "text/csv; charset=utf-8"})
