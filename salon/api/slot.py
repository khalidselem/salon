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


@frappe.whitelist(allow_guest=True)
def get_branch_configuration(branch_id=None, employee_id=None):
    try:
        if not branch_id:
            frappe.response["status"] = False
            frappe.response["message"] = "branch_id is required"
            frappe.response["data"] = []
            return

        branch_doc = frappe.get_doc("Branches", branch_id)

      
        slot_ids = [row.time_slot for row in getattr(branch_doc, "slot_time", []) if row.time_slot]

        if not slot_ids:
            frappe.response["status"] = True
            frappe.response["message"] = "No time slots found for this branch"
            frappe.response["data"] = []
            return

        slots = frappe.get_all(
            "Time Slot",
            filters={"name": ["in", slot_ids], "disable": 0},
            fields=["name as id", "service_time as start_time", "duration"]
        )

        slot_data = []
        for s in slots:
            start = s.get("start_time")
            duration = s.get("duration") or 0
            end = None
            try:
               if start:
                    parts = start.split(":")
                    hours = int(parts[0])
                    minutes = int(parts[1])
                    total_minutes = hours * 60 + minutes + duration
                    end_hour = (total_minutes // 60) % 24
                    end_minute = total_minutes % 60
                    end = f"{end_hour:02d}:{end_minute:02d}:00"
               else:
                    end = ""
            except Exception:
                end = ""

            slot_data.append({
                "branch_id": branch_id,
                "id": s.get("id"),
                "start_time": start,
                "end_time": end,
                "duration": duration,
                "is_available": True
            })

        frappe.response["status"] = True
        frappe.response["message"] = "list fetched successfully"
        frappe.response["data"] = slot_data

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "get_branch_configuration Error")
        frappe.response["status"] = False
        frappe.response["message"] = f"Server Error: {str(e)}"
        frappe.response["data"] = []
