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

@frappe.whitelist(allow_guest=True)
def get_employee_list(branch_id=None, service_ids=None):
    try:
        site_url = frappe.utils.get_url()

        # ✅ Only active employees
        filters = {"status": "Active"}

        # Base query
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

        # 🔹 Filter by Branch
        if branch_id:
            branch_doc = frappe.get_doc("Branches", branch_id)
            employee_names = [row.employee for row in branch_doc.staff]
            if employee_names:
                query = query.where(Field("name").isin(employee_names))
            else:
                return {
                    "status": True,
                    "message": "list fetched successfully",
                    "data": [],
                }

        # 🔹 Filter by Service
        if service_ids:
            service_ids = [s.strip() for s in service_ids.split(",") if s.strip()]
            employees_for_services = set()

            for sid in service_ids:
                try:
                    service_doc = frappe.get_doc("Services", sid)
                    for row in service_doc.staff:
                        employees_for_services.add(row.employee)
                except Exception:
                    pass

            if employees_for_services:
                query = query.where(Field("name").isin(list(employees_for_services)))
            else:
                return {
                    "status": True,
                    "message": "list fetched successfully",
                    "data": [],
                }

        # Run query
        employees = query.run(as_dict=True)
        data = []

        # ✅ Format each employee for Flutter
        for emp in employees:
            data.append({
                "id": emp.name,
                "first_name": emp.first_name,
                "last_name": emp.last_name,
                "full_name": emp.employee_name,
                "email": frappe.db.get_value("User", emp.user_id, "email") if emp.user_id else None,
                "mobile": emp.cell_number,
                "gender": emp.gender,
                "date_of_birth": emp.date_of_birth,
                "joining_date": emp.date_of_joining,
                "profile_image": f"{site_url}{emp.image}" if emp.image else "",
                "holiday": "Friday",
                "status": 1,
                "rating_star": 5,
            })

        frappe.response["status"] = True
        frappe.response["message"] = "Employee List fetched successfully"
        frappe.response["data"] = data

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Employee Detail Error")
        frappe.response["status"] = False
        frappe.response["message"] = f"Server Error: {str(e)}"
        frappe.response["data"] = {} 