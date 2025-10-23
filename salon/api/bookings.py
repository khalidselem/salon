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

@frappe.whitelist(allow_guest=False)
def save_booking(data=None):
    try:
        if isinstance(data, str):
            data = frappe.parse_json(data)

        required_fields = ["customer", "state", "branch", "staff", "date", "slot", "table_services"]
        for field in required_fields:
            if not data.get(field):
                frappe.throw(f"Missing required field: {field}")

        # Create new booking doc
        doc = frappe.new_doc("Booking")
        doc.customer = data.get("customer")
        doc.state = data.get("state")
        doc.branch = data.get("branch")
        doc.driver = data.get("driver")
        doc.location = data.get("location")
        doc.lat_lng = data.get("lat_lng")
        doc.staff = data.get("staff")
        doc.date = data.get("date")
        doc.slot = data.get("slot")
        doc.status = data.get("status", "Pending")
        doc.payment_status = data.get("payment_status", "Unpaid")
        doc.payment_reference = data.get("payment_reference")
        doc.payment_method = data.get("payment_method")
        doc.note = data.get("note")
        doc.is_gift = data.get("is_gift", 0)
        doc.gift_to = data.get("gift_to")
        doc.gift_from = data.get("gift_from")
        doc.gift_message = data.get("gift_message")
        doc.gift_number = data.get("gift_number")
        doc.gift_location = data.get("gift_location")

        # Gift card handling (base64 → file)
        gift_card_base64 = data.get("gift_card")
        if gift_card_base64:
            filename = f"gift_card_{frappe.generate_hash('', 8)}.png"
            filedata = base64.b64decode(gift_card_base64)
            file_doc = frappe.get_doc({
                "doctype": "File",
                "file_name": filename,
                "attached_to_doctype": "Booking",
                "attached_to_name": doc.name or "New Booking",
                "is_private": 0,
                "content": filedata
            })
            file_doc.save(ignore_permissions=True)
            doc.gift_card = file_doc.file_url

        # Handle Booking Items List
        total_amount = 0
        for s in data.get("table_services", []):
            qty = float(s.get("qty", 1))
            price = float(s.get("price", 0))
            total_price = qty * price
            total_amount += total_price

            doc.append("table_services", {
                "service": s.get("service"),
                "qty": qty,
                "price": price,
                "total_price": total_price
            })

        doc.total = total_amount

        doc.insert(ignore_permissions=True)
        frappe.db.commit()

        return {
            "status": True,
            "message": "Booking saved successfully",
            "data": {"booking_id": doc.name}
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "save_booking")
        return {
            "status": False,
            "message": f"Server Error: {str(e)}",
            "data": []
        }
