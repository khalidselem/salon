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
        raw_data = frappe.request.data

        # ✅ Decode JSON bytes if sent from Flutter
        if raw_data:
            try:
                if isinstance(raw_data, bytes):
                    raw_data = raw_data.decode("utf-8")
                data = json.loads(raw_data)
            except Exception:
                data = frappe.form_dict
        else:
            data = frappe.form_dict

        # ✅ Check if we got a valid dictionary
        if not data or not isinstance(data, dict):
            frappe.response.update({
                "status": False,
                "message": "Invalid or empty request body",
                "data": []
            })
            return

        # ✅ Create new booking document
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

        # ✅ Handle gift card image
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

        # ✅ Handle Booking Items
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

@frappe.whitelist()
def booking_list(email=None, search=None):
    try:
        if not email:
            return {
                "status": False,
                "message": "Email is required",
                "data": []
            }

        filters = {"customer": email}
        if search:
            filters["name"] = ["like", f"%{search}%"]

        bookings = frappe.get_all(
            "Booking",
            filters=filters,
            fields=[
                "name as id",
                "customer",
                "state",
                "state_name",
                "location",
                "staff_name",
                "staff",
                "date",
                "slot",
                "status",
                "driver_note",
                "payment_status",
                "payment_reference",
                "payment_method",
                "cash_method",
                "branch",
                "note",
                "total",
                "is_gift",
                "gift_to",
                "gift_from",
                "gift_location",
                "gift_message",
                "gift_number",
            ],
            order_by="creation desc",
        )

        result = []
        for b in bookings:
            result.append({
                "id": b.id or "",
                "customer": b.customer or "",
                "state": b.state or "",
                "state_name": b.state_name or "",
                "location": b.location or "",
                "staff_name": b.staff_name or "",
                "staff": b.staff or "",
                "date": str(b.date) if b.date else "",
                "slot": b.slot or "",
                "status": b.status or "",
                "driver_note": b.driver_note or "",
                "payment_status": b.payment_status or "",
                "payment_reference": b.payment_reference or "",
                "payment_method": b.payment_method or "",
                "cash_method": b.cash_method or "",
                "branch": b.branch or "",
                "note": b.note or "",
                "total": b.total or 0,
                "is_gift": b.is_gift or 0,
                "gift_to": b.gift_to or "",
                "gift_from": b.gift_from or "",
                "gift_location": b.gift_location or "",
                "gift_message": b.gift_message or "",
                "gift_number": b.gift_number or "",
                "table_services": get_booking_services(b.id),
            })

        return {
            "status": True,
            "message": "Booking list fetched successfully",
            "data": result,
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "booking_list API Error")
        return {
            "status": False,
            "message": f"Server Error: {str(e)}",
            "data": []
        }


def get_booking_services(booking_id):
    """Return services in booking with default empty structure"""
    try:
        services = frappe.get_all(
            "Booking Items List",
            filters={"parent": booking_id},
            fields=["service", "qty", "price"]
        )

        result = []
        for s in services:
            service_name = frappe.db.get_value("Service", s.service, "english_name") or ""
            result.append({
                "service_name": service_name,
                "qty": s.qty or 0,
                "price": s.price or 0,
            })

        return result
    except Exception:
        return []

