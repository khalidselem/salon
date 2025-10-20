import json
import base64
import os
from collections.abc import Iterable
from six import string_types
import frappe
from frappe.utils import flt
from frappe import _
from frappe.utils import get_files_path
from frappe.utils.file_manager import save_file
from frappe.utils import nowdate, nowtime, get_first_day, getdate
from frappe.query_builder import Field

def log_error(title, error):
    frappe.log_error(frappe.get_traceback(), title)

def flatten(lis):
    for item in lis:
        if isinstance(item, Iterable) and not isinstance(item, str):
            for x in flatten(item):
                yield x
        else:        
            yield item

from frappe.query_builder import Field
import frappe

@frappe.whitelist(allow_guest=True)
def get_employee_list(branch_id=None, service_ids=None):
    try:
        site_url = frappe.utils.get_url()

        # base active filter using QueryBuilder
        query = (
            frappe.qb.from_("tabEmployee")
            .select(
                "name",
                "first_name",
                "last_name",
                "employee_name",
                "user_id",
                "cell_number",
                "date_of_birth",
                "gender",
                "date_of_joining",
                "image",
                "status",
            )
            .where(Field("status") == "Active")
        )

        # --- BRANCH: resolve branch_doc robustly ---
        branch_employee_names = None
        if branch_id:
            branch_doc = None
            # 1) try as docname
            try:
                branch_doc = frappe.get_doc("Branches", branch_id)
            except Exception:
                branch_doc = None

            # 2) try numeric lookup by common fields if doc not found
            if not branch_doc:
                # attempt common field names that may contain numeric id
                for fld in ("id", "branch_id", "idx", "name1"):
                    try:
                        val = frappe.db.get_value("Branches", {fld: branch_id}, "name")
                        if val:
                            try:
                                branch_doc = frappe.get_doc("Branches", val)
                                break
                            except Exception:
                                branch_doc = None
                    except Exception:
                        pass

            # 3) fallback: try to find a branch whose name or name_english/name1 contains the branch_id string
            if not branch_doc:
                matches = frappe.get_all(
                    "Branches",
                    filters=[["name", "like", f"%{branch_id}%"]],
                    limit_page_length=1,
                )
                if matches:
                    try:
                        branch_doc = frappe.get_doc("Branches", matches[0].name)
                    except Exception:
                        branch_doc = None

            # Log what we found for debugging
            frappe.logger().debug(f"[get_employee_list] branch_id param: {branch_id}; resolved branch_doc: {getattr(branch_doc, 'name', None)}")

            # If we indeed have a branch_doc, extract staff child table
            if branch_doc:
                staff_rows = getattr(branch_doc, "staff", []) or []
                # staff_rows may be list of DocTypes/Row objects or dicts
                branch_employee_names = []
                for r in staff_rows:
                    # row could be a Document or dict
                    emp = getattr(r, "employee", None) or r.get("employee") if isinstance(r, dict) else None
                    if not emp:
                        # try common alt fieldnames
                        emp = getattr(r, "employee_name", None) or (r.get("employee_name") if isinstance(r, dict) else None)
                    if emp:
                        branch_employee_names.append(emp)
                frappe.logger().debug(f"[get_employee_list] branch staff rows count: {len(staff_rows)} resolved employees: {branch_employee_names}")

            else:
                # branch not found — log that and return empty list (matching expected shape)
                frappe.logger().debug(f"[get_employee_list] branch lookup failed for param: {branch_id}")
                frappe.response["status"] = True
                frappe.response["message"] = "list fetched successfully"
                frappe.response["data"] = []
                return

            # If branch found but no linked employees, return empty list
            if not branch_employee_names:
                frappe.logger().debug(f"[get_employee_list] found branch but no staff linked.")
                frappe.response["status"] = True
                frappe.response["message"] = "list fetched successfully"
                frappe.response["data"] = []
                return

            # Apply branch filter to query
            query = query.where(Field("name").isin(branch_employee_names))

        # --- SERVICE: collect employees assigned to service(s) ---
        if service_ids:
            employees_for_services = set()
            # allow comma separated list or a single value
            service_list = [s.strip() for s in (service_ids or "").split(",") if s.strip()]
            for sid in service_list:
                service_doc = None
                # try docname
                try:
                    service_doc = frappe.get_doc("Service", sid)
                except Exception:
                    service_doc = None

                # fallback: try find by english_name or name like
                if not service_doc:
                    matches = frappe.get_all("Service", filters=[["name", "like", f"%{sid}%"]], limit_page_length=1)
                    if matches:
                        try:
                            service_doc = frappe.get_doc("Service", matches[0].name)
                        except Exception:
                            service_doc = None

                if not service_doc:
                    frappe.logger().debug(f"[get_employee_list] service lookup failed for: {sid}")
                    continue

                # staff child table on Service doc
                staff_rows = getattr(service_doc, "staff", []) or []
                for r in staff_rows:
                    emp = getattr(r, "employee", None) or (r.get("employee") if isinstance(r, dict) else None)
                    if emp:
                        employees_for_services.add(emp)

                frappe.logger().debug(f"[get_employee_list] service {sid} staff count: {len(staff_rows)}")

            if not employees_for_services:
                frappe.logger().debug("[get_employee_list] no employees found for given services")
                frappe.response["status"] = True
                frappe.response["message"] = "list fetched successfully"
                frappe.response["data"] = []
                return

            # apply service filter
            query = query.where(Field("name").isin(list(employees_for_services)))

        # Execute
        employees = query.run(as_dict=True)
        data = []

        for emp in employees:
            data.append({
                "id": emp.get("name"),
                "first_name": emp.get("first_name"),
                "last_name": emp.get("last_name"),
                "full_name": emp.get("employee_name"),
                "email": frappe.db.get_value("User", emp.get("user_id"), "email") if emp.get("user_id") else None,
                "mobile": emp.get("cell_number"),
                "gender": emp.get("gender"),
                "date_of_birth": emp.get("date_of_birth"),
                "joining_date": emp.get("date_of_joining"),
                "profile_image": f"{site_url}{emp.get('image')}" if emp.get("image") else "",
                "holiday": "Friday",
                "status": 1,
                "rating_star": 5,
            })

        # *** IMPORTANT: set frappe.response to control top-level JSON (no "message" wrapper) ***
        frappe.response["status"] = True
        frappe.response["message"] = "list fetched successfully"
        frappe.response["data"] = data

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "get_employee_list Error")
        frappe.response["status"] = False
        frappe.response["message"] = f"Server Error: {str(e)}"
        frappe.response["data"] = []
