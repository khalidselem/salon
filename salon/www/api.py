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
def get_user(user):
    doc = frappe.get_doc("User", user)
    return {"user": doc, "type": "user"}

@frappe.whitelist()
def get_items_list(filters=None):
    return frappe.db.get_list("Item", filters=filters, fields="name")

@frappe.whitelist()
def create_payment(args):
    if isinstance(args, string_types):
        args = json.loads(args)

    if not frappe.has_permission("Payment Entry", ptype="write", user=args.get("owner", frappe.session.user)):
        return {"error": "Not Permitted", "status": 0}

    try:
        doc = frappe.new_doc("Payment Entry")

        # Basic required fields
        doc.payment_type = args.get("payment_type")
        doc.posting_date = args.get("posting_date") or nowdate()
        doc.mode_of_payment = args.get("mode_of_payment")
        doc.party_type = args.get("party_type")
        doc.party = args.get("party")
        doc.party_name = args.get("party_name")
        doc.paid_from = args.get("paid_from")
        doc.paid_to = args.get("paid_to")
        doc.paid_amount = args.get("paid_amount")
        doc.received_amount = args.get("paid_amount")

        if args.get("reference_no"):
            doc.reference_no = args.get("reference_no")
            doc.reference_date = nowdate()

        # Insert and Submit
        doc.insert()
        frappe.db.commit()

        return {
            "status": 1,
            "name": doc.name,
            "message": f"Payment Entry {doc.name} created successfully."
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Create Payment Entry Error")
        return {"status": 0, "error": str(e)}

@frappe.whitelist()
def update_payment(args):
    if isinstance(args, string_types):
        args = json.loads(args)

    if not frappe.has_permission("Payment Entry", ptype= "write", user=args.get("owner")):
        return {"error": "Not Permitted", "status": 0}

    if not args.get("payment_entry"):
        return {"error": "No Payment Entry is Specified", "status": 0}

    if not frappe.db.exists("Payment Entry", args.get("payment_entry")):
        return {"error": "No Payment Entry with the Name {}".format(args.get("payment_entry")), "status": 0}

    payment_entry = frappe.get_doc("Payment Entry", args.get("payment_entry"))

    for field in args:
        if field == "payment_entry": continue

        elif hasattr(payment_entry, field):
            setattr(payment_entry, field, args.get(field))

    try:
        payment_entry.save()
        frappe.db.commit()
    except Exception as e:
        return {"error": e, "status": 0}

    return {"error": 0, "status": 1}

@frappe.whitelist()
def get_payment_entries_list(filters=None):
    return frappe.db.get_list("Payment Entry", filters=filters, fields=["name", "posting_date", "party_name", "payment_type", "status"])

@frappe.whitelist()
def get_payment_entry(payment_entry):
    return frappe.get_all("Payment Entry", filters={"name": payment_entry}, fields=["*"])

#branches api 


branches = frappe.db.get_list(
    "Branches",
    filters=filters,
    fields=["*"]
)






