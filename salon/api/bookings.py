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


def log_error(title, error):
    frappe.log_error(frappe.get_traceback(), title)

def flatten(lis):
    for item in lis:
        if isinstance(item, Iterable) and not isinstance(item, str):
            for x in flatten(item):
                yield x
        else:        
            yield item

@frappe.whitelist(allow_guest=False)
def get_states(id=None):
    try:
        if not id:
            frappe.response["status"] = False
            frappe.response["message"] = "Missing required parameter: id (branch_id)"
            frappe.response["data"] = []
            return

        states = frappe.get_all(
            "States",
            filters={"branch": id},
            fields=["name", "state_name", "branch", "branch_name"]
        )

        frappe.response["status"] = True
        frappe.response["message"] = "States fetched successfully"
        frappe.response["data"] = states

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get States Error")
        frappe.response["status"] = False
        frappe.response["message"] = f"Server Error: {str(e)}"
        frappe.response["data"] = []

import frappe

@frappe.whitelist(allow_guest=False)
def get_available_driver(id=None, employee_id=None):
    try:
        if not id:
            frappe.response.update({
                "status": False,
                "message": "Missing required parameter: id (state id)",
                "data": []
            })
            return

        state_id = str(id)
        emp_id = str(employee_id) if employee_id else None

        drivers = frappe.get_all(
            "Drivers",
            fields=["name", "driver_name", "user", "device_token"]
        )

        available_drivers = []

        for d in drivers:
            driver_doc = frappe.get_doc("Drivers", d.name)

            has_state = any(
                state_id in [str(v) for v in row.as_dict().values()]
                for row in driver_doc.get("states")
            )

            has_employee = True
            if emp_id:
                has_employee = any(
                    emp_id in [str(v) for v in row.as_dict().values()]
                    for row in driver_doc.get("staff")
                )

            if has_state and has_employee:
                available_drivers.append({
                    "driver_id": d.name,
                    "driver_name": d.driver_name,
                    "user": d.user,
                    "device_token": d.device_token,
                })

        frappe.response.update({
            "status": True,
            "message": "Drivers fetched successfully",
            "data": available_drivers
        })

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get Available Driver Error")
        frappe.response.update({
            "status": False,
            "message": f"Server Error: {str(e)}",
            "data": []
        })

@frappe.whitelist(allow_guest=True)
def save_booking():
    try:
        # Parse input safely
        raw_data = frappe.request.data

        if not raw_data:
            frappe.response.update({
                "status": False,
                "message": "No request data found",
                "data": []
            })
            return

        try:
            data = frappe.parse_json(raw_data)
        except Exception:
            data = frappe.form_dict

        if not data or not isinstance(data, dict):
            frappe.response.update({
                "status": False,
                "message": "Invalid or empty request body",
                "data": []
            })
            return

        # Create new booking doc
        doc = frappe.new_doc("Booking")

        safe_fields = [
            "customer", "state", "branch", "driver", "location",
            "lat_lng", "staff", "date", "slot", "status",
            "payment_status", "payment_reference", "payment_method",
            "note", "is_gift", "gift_from", "gift_to",
            "gift_message", "gift_location", "gift_number"
        ]

        for field in safe_fields:
            if field in data:
                doc.set(field, data[field])

        # Handle gift card image if present
        gift_card = data.get("gift_card")
        if gift_card:
            try:
                img_data = base64.b64decode(gift_card)
                file_name = f"{frappe.generate_hash()}.png"
                file_path = frappe.utils.get_site_path("public", "files", file_name)
                with open(file_path, "wb") as f:
                    f.write(img_data)
                doc.gift_card = f"/files/{file_name}"
            except Exception as e:
                frappe.log_error(f"Gift card decode failed: {str(e)}")

        # Handle Booking Items safely
        total_amount = 0.0
        services = data.get("table_services") or []

        if not isinstance(services, list):
            frappe.response.update({
                "status": False,
                "message": "Invalid data: table_services must be a list",
                "data": []
            })
            return

        for s in services:
            if not isinstance(s, dict):
                continue

            service_id = s.get("service")
            qty = float(s.get("qty") or 1)
            price = float(s.get("price") or 0)
            total_price = qty * price
            total_amount += total_price

            doc.append("table_services", {
                "service": service_id,
                "qty": qty,
                "price": price,
                "total_price": total_price
            })

        doc.total = total_amount
        doc.insert(ignore_permissions=True)
        frappe.db.commit()

        frappe.response.update({
            "status": True,
            "message": "Booking saved successfully",
            "data": {"name": doc.name}
        })

    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(frappe.get_traceback(), "save_booking_error")
        frappe.response.update({
            "status": False,
            "message": f"Server Error: {str(e)}",
            "data": []
        })
