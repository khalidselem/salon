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

@frappe.whitelist()
def create_sales_invoice(args):
    if isinstance(args, string_types):
        args = json.loads(args)

    if not frappe.has_permission("Sales Invoice", ptype= "write", user=args.get("owner")):
        return {"error": "Not Permitted", "status": 0}

    doc = frappe.new_doc("Sales Invoice")

    tables = doc.meta.get_table_fields()
    tables_names = {}
    if tables:
        for df in tables:
            tables_names[df.fieldname] = df.options

    for field in args:
        if field in tables_names:
            for d in args.get(field):
                new_doc = frappe.new_doc(tables_names[field], as_dict=True)
                for attr in d:
                    if hasattr(new_doc, attr):
                        setattr(new_doc, attr, d[attr])

                doc.append(field, new_doc)

        elif hasattr(doc, field):
            setattr(doc, field, args.get(field))

    try:
        doc.insert()
        frappe.db.commit()
    except Exception as e:
        return {"error": e, "status": 0}

    return {"error": 0, "status": 1}

@frappe.whitelist()
def update_sales_invoice(args):
    if isinstance(args, string_types):
        args = json.loads(args)

    if not frappe.has_permission("Sales Invoice", ptype= "write", user=args.get("owner")):
        return {"error": "Not Permitted", "status": 0}

    if not args.get("sales_invoice"):
        return {"error": "No Sales Invoice is Specified", "status": 0}

    if not frappe.db.exists("Sales Invoice", args.get("sales_invoice")):
        return {"error": "No Sales Invoice with the Name {}".format(args.get("sales_invoice")), "status": 0}

    sales_invoice = frappe.get_doc("Sales Invoice", args.get("sales_invoice"))

    for field in args:
        if field == "sales_invoice": continue

        elif hasattr(sales_invoice, field):
            setattr(sales_invoice, field, args.get(field))

    try:
        sales_invoice.save()
        frappe.db.commit()
    except Exception as e:
        return {"error": e, "status": 0}

    return {"error": 0, "status": 1}

@frappe.whitelist()
def get_default_company():
    return {
        "company": frappe.db.get_single_value("Global Defaults", "default_company")
    }

@frappe.whitelist()
def get_sales_invoices_list(filters=None):
    return frappe.db.get_list("Sales Invoice", filters=filters, fields="name")

@frappe.whitelist()
def get_sales_invoice(sales_invoice):
    return frappe.get_all("Sales Invoice", filters={"name": sales_invoice}, fields=["*"])

@frappe.whitelist()
def create_purchase_invoice(args):
    if isinstance(args, string_types):
        args = json.loads(args)

    if not frappe.has_permission("Purchase Invoice", ptype= "write", user=args.get("owner")):
        return {"error": "Not Permitted", "status": 0}

    doc = frappe.new_doc("Purchase Invoice")

    tables = doc.meta.get_table_fields() or []
    tables_names = {}
    if tables:
        for df in tables:
            tables_names[df.fieldname] = df.options

    for field in args:
        if field in tables_names:
            for d in args.get(field):
                new_doc = frappe.new_doc(tables_names[field], as_dict=True)
                for attr in d:
                    if hasattr(new_doc, attr):
                        setattr(new_doc, attr, d[attr])

                doc.append(field, new_doc)

        elif hasattr(doc, field):
            setattr(doc, field, args.get(field))

    try:
        doc.insert()
        frappe.db.commit()
    except Exception as e:
        return {"error": e, "status": 0}

    return {"error": 0, "status": 1}

@frappe.whitelist()
def update_purchase_invoice(args):
    if isinstance(args, string_types):
        args = json.loads(args)

    if not frappe.has_permission("Purchase Invoice", ptype= "write", user=args.get("owner")):
        return {"error": "Not Permitted", "status": 0}

    if not args.get("purchase_invoice"):
        return {"error": "No Purchase Invoice is Specified", "status": 0}

    if not frappe.db.exists("Purchase Invoice", args.get("purchase_invoice")):
        return {"error": "No Purchase Invoice with the Name {}".format(args.get("purchase_invoice")), "status": 0}

    purchase_invoice = frappe.get_doc("Purchase Invoice", args.get("purchase_invoice"))

    for field in args:
        if field == "purchase_invoice": continue

        elif hasattr(purchase_invoice, field):
            setattr(purchase_invoice, field, args.get(field))

    try:
        purchase_invoice.save()
        frappe.db.commit()
    except Exception as e:
        return {"error": e, "status": 0}

    return {"error": 0, "status": 1}

@frappe.whitelist()
def get_purchase_invoices_list(filters=None):
    return frappe.db.get_list("Purchase Invoice", filters=filters, fields="name")

@frappe.whitelist()
def get_purchase_invoice(purchase_invoice):
    return frappe.get_all("Purchase Invoice", filters={"name": purchase_invoice}, fields=["*"])

@frappe.whitelist()
def get_exchange_rate(from_currency, to_currency, transaction_date = None):
    from erpnext.setup.utils import get_exchange_rate

    return get_exchange_rate(from_currency, to_currency, transaction_date)

@frappe.whitelist()
def get_payment_party_details(party_type, party, date, company=None, cost_center=None):
    from erpnext.accounts.doctype.payment_entry.payment_entry import get_party_details

    return get_party_details(company, party_type, party, date, cost_center)

@frappe.whitelist()
def get_paid_to_accounts_query(payment_type, party_type, company=None):
    if not company:
        from erpnext import get_default_company

        company = get_default_company()

    if payment_type in ["Receive", "Internal Transfer"]:
        account_types = ["Bank", "Cash"]

    else:
        if party_type == "Customer":
            account_types =  ["Receivable"]
        else: account_types = ["Payable"]

    return frappe.db.get_all("Account", {
        "company": company,
        "is_group": 0,
        "account_type": ("in", account_types)
    }, "name", as_list = 1)  

@frappe.whitelist()
def get_paid_from_accounts_query(payment_type, party_type, company=None):
    if not company:
        from erpnext import get_default_company

        company = get_default_company()

    if payment_type in ["Pay", "Internal Transfer"]:
        account_types = ["Bank", "Cash"]

    else:
        if party_type == "Customer":
            account_types =  ["Receivable"]
        else: account_types = ["Payable"]

    return frappe.db.get_all("Account", {
        "company": company,
        "is_group": 0,
        "account_type": ("in", account_types)
    }, "name", as_list = 1)  

@frappe.whitelist()
def get_outstanding_documents(args):
    from erpnext.accounts.doctype.payment_entry.payment_entry import get_outstanding_reference_documents

    return get_outstanding_reference_documents(args)

@frappe.whitelist()
def get_conversion_factor(item_code, uom):
    from erpnext.stock.get_item_details import get_conversion_factor

    return get_conversion_factor(item_code, uom)

@frappe.whitelist()
def get_item_details(args):
    from erpnext.stock.get_item_details import get_item_details

    return get_item_details(args)

@frappe.whitelist()
def get_party_details(party_type, party, posting_date=None, company=None, account=None, price_list=None, pos_profile=None, doctype=None):
    from erpnext.accounts.party import get_party_details

    return get_party_details(party_type=party_type, party=party, posting_date=posting_date, company=company, account=account, price_list=price_list, pos_profile=pos_profile, doctype=doctype)

@frappe.whitelist()
def get_party_account(party_type, party, company):
    from erpnext.accounts.party import get_party_account

    return get_party_account(party_type, party, company)

@frappe.whitelist()
def get_defaults_company_currency():
    from erpnext import get_default_company

    company = get_default_company()
    
    if company:
        return company, frappe.get_cached_value("Company", company, "default_currency")

@frappe.whitelist()
def get_bank_accounts_list(filters=None):
    return frappe.db.get_list("Bank Account", filters=filters, fields="name")

@frappe.whitelist()
def get_accounts_list(filters=None):
    return frappe.db.get_list("Account", filters=filters, fields="name")

@frappe.whitelist()
def get_mode_of_payments_list(company, filters=None):
    modes = frappe.get_all("Mode of Payment", filters=filters, fields=["name", "type"])
    result = []

    for mode in modes:
        account = frappe.get_value(
            "Mode of Payment Account",
            filters={
                "parent": mode.name,               
                "company": company
            },
            fieldname="default_account"
        )

        result.append({
            "name": mode.name,
            "type": mode.type,
            "account": account
        })

    return result

@frappe.whitelist()
def get_employees_list(filters=None):
    return frappe.db.get_list("Employee", filters=filters, fields="name")

@frappe.whitelist()
def get_suppliers_list(filters=None):
    return frappe.db.get_list("Supplier", filters=filters, fields=["name", "supplier_name"])

@frappe.whitelist()
def get_shareholders_list(filters=None):
    return frappe.db.get_list("Shareholder", filters=filters, fields="name")

@frappe.whitelist()
def get_customers_list(filters=None):
    return frappe.db.get_list("Customer", filters=filters, fields=["name", "customer_name"])

@frappe.whitelist()
def get_currencies_list(filters=None):
    return frappe.db.get_list("Currency", filters=filters, fields="name")

@frappe.whitelist()
def get_price_lists_list(filters=None):
    return frappe.db.get_list("Price List", filters=filters, fields="name")

@frappe.whitelist()
def get_uoms_list(filters=None):
    return frappe.db.get_list("UOM", filters=filters, fields="name")

@frappe.whitelist()
def get_sales_persons_list(filters=None):
    return frappe.db.get_list("Sales Person", filters=filters, fields="name")

@frappe.whitelist()
def get_sales_taxes_templates_list(filters=None):
    return frappe.db.get_list("Sales Taxes and Charges Template", filters=filters, fields="name")

@frappe.whitelist()
def get_purchase_taxes_templates_list(filters=None):
    return frappe.db.get_list("Purchase Taxes and Charges Template", filters=filters, fields="name")

@frappe.whitelist()
def get_addresses_list(filters=None):
    return frappe.db.get_list("Address", filters=filters, fields="name")

@frappe.whitelist()
def get_contacts_list(filters=None):
    return frappe.db.get_list("Contact", filters=filters, fields="name")

@frappe.whitelist()
def get_payment_terms_templates_list(filters=None):
    return frappe.db.get_list("Payment Terms Template", filters=filters, fields="name")

@frappe.whitelist()
def get_payment_terms_list(filters=None):
    return frappe.db.get_list("Payment Term", filters=filters, fields="name")

@frappe.whitelist()
def get_terms_and_conditions_list(filters=None):
    return frappe.db.get_list("Terms and Conditions", filters=filters, fields="name")

@frappe.whitelist()
def get_tax_templates():
    try:
        templates = frappe.get_all("Sales Taxes and Charges Template", fields=["name", "title"], order_by="creation desc")

        result = []
        for t in templates:
            doc = frappe.get_doc("Sales Taxes and Charges Template", t.name)
            result.append({
                "name": doc.name,
                "title": doc.title,
                "taxes": [
                    {
                        "charge_type": tax.charge_type,
                        "account_head": tax.account_head,
                        "description": tax.description,
                        "rate": tax.rate
                    } for tax in doc.taxes
                ]
            })

        return {
            "status": "success",
            "templates": result
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get Tax Templates Error")
        return {
            "status": "error",
            "message": str(e)
        }

@frappe.whitelist()
def get_cost_centers_list(filters=None):
    return frappe.db.get_list("Cost Center", filters=filters, fields="name")

@frappe.whitelist()
def get_projects_list(filters=None):
    return frappe.db.get_list("Project", filters=filters, fields="name")

@frappe.whitelist()
def get_default_country():
    try:
        default_country = frappe.db.get_single_value("System Settings", "country")
        return {
            "status": "success",
            "default_country": default_country
        }
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get Default Country Error")
        return {
            "status": "error",
            "message": str(e)
        }

@frappe.whitelist()
def get_warehouses():
    return frappe.get_all("Warehouse", fields="name")

@frappe.whitelist()
def create_customer(customer_name, phone, address_line1, city=None, country=None):
    try:
        # Get first available Customer Group
        customer_group = frappe.get_value("Customer Group", {}, "name", order_by="creation asc")
        if not customer_group:
            return {
                "status": "error",
                "message": "No Customer Group found in the system."
            }

        # Get first available Territory
        territory = frappe.get_value("Territory", {}, "name", order_by="creation asc")
        if not territory:
            return {
                "status": "error",
                "message": "No Territory found in the system."
            }

        # If no country passed, use default from System Settings
        if not country:
            country = frappe.db.get_single_value("System Settings", "country")

        # Create the Customer
        customer = frappe.get_doc({
            "doctype": "Customer",
            "customer_name": customer_name,
            "customer_type": "Individual",
            "mobile_no": phone,
            "customer_group": customer_group,
            "territory": territory
        })
        customer.insert(ignore_permissions=True)

        # Create Address
        address = frappe.get_doc({
            "doctype": "Address",
            "address_title": customer_name,
            "address_type": "Billing",
            "address_line1": address_line1,
            "city": city,
            "country": country,
            "links": [{
                "link_doctype": "Customer",
                "link_name": customer.name
            }]
        })
        address.insert(ignore_permissions=True)

        return {
            "status": "success",
            "customer_id": customer.name,
            "customer_name": customer.customer_name
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Create Customer API Error")
        return {
            "status": "error",
            "message": str(e)
        }

@frappe.whitelist()
def get_all_customers():
    try:
        customers = frappe.get_all(
            "Customer",
            fields=["name", "customer_name", "mobile_no"],
            order_by="creation desc"
        )

        result = []
        for cust in customers:
            address = frappe.db.sql("""
                SELECT addr.address_line1, addr.city, addr.country
                FROM `tabAddress` addr
                JOIN `tabDynamic Link` dl ON dl.parent = addr.name
                WHERE dl.link_doctype = 'Customer' AND dl.link_name = %s
                LIMIT 1
            """, cust.name, as_dict=True)

            result.append({
                "customer_id": cust.name,
                "customer_name": cust.customer_name,
                "phone": cust.mobile_no,
                "address_line1": address[0].address_line1 if address else None,
                "city": address[0].city if address else None,
                "country": address[0].country if address else None
            })

        return {
            "status": "success",
            "customers": result
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get All Customers Error")
        return {
            "status": "error",
            "message": str(e)
        }

@frappe.whitelist()
def get_items_details_list(filters=None):
    import json

    try:
        if isinstance(filters, str):
            filters = json.loads(filters)

        items = frappe.get_list(
            "Item", 
            filters=filters, 
            fields=["name", "item_name", "item_group", "image", "stock_uom"], 
            order_by="creation desc"
        )

        result = []
        for item in items:
            # Get latest selling price
            item_price = frappe.db.sql("""
                SELECT price_list_rate 
                FROM `tabItem Price` 
                WHERE item_code=%s AND selling=1
                ORDER BY modified DESC 
                LIMIT 1
            """, (item["name"],), as_dict=True)

            rate = item_price[0]["price_list_rate"] if item_price else 0

            # Get barcodes
            barcodes = frappe.get_all(
                "Item Barcode", 
                filters={"parent": item["name"]}, 
                fields=["barcode"]
            )

            # Get first Item Tax Template for the item
            item_tax = frappe.db.sql("""
                SELECT item_tax_template
                FROM `tabItem Tax`
                WHERE parent=%s
                ORDER BY idx ASC
                LIMIT 1
            """, (item["name"],), as_dict=True)

            tax_template = None
            tax_rate = 0
            tax_account = None

            if item_tax:
                tax_template = item_tax[0]["item_tax_template"]

                # Fetch first tax rate from the template details
                tax_detail = frappe.db.sql("""
                    SELECT tax_type, tax_rate
                    FROM `tabItem Tax Template Detail`
                    WHERE parent=%s
                    ORDER BY idx ASC
                    LIMIT 1
                """, (tax_template,), as_dict=True)

                if tax_detail:
                    tax_account = tax_detail[0]["tax_type"]
                    tax_rate = tax_detail[0]["tax_rate"]

            result.append({
                "name": item["name"],
                "item_name": item["item_name"],
                "item_group": item["item_group"],
                "image": item["image"],
                "stock_uom": item["stock_uom"],
                "standard_rate": rate,
                "barcodes": [b["barcode"] for b in barcodes] if barcodes else [],
                "item_tax_template": tax_template,
                "tax_account": tax_account,
                "tax_rate": tax_rate
            })

        return {
            "status": "success",
            "items": result
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get Items Details List Error")
        return {
            "status": "error",
            "message": str(e)
        }

@frappe.whitelist()
def create_sales_invoice(data):
    try:
        if isinstance(data, str):
            data = json.loads(data)

        customer = data.get("customer")
        items = data.get("items", [])
        if not customer or not items:
            return {"status": "error", "message": "Customer and items are required."}

        posting_date = data.get("posting_date")
        posting_time = data.get("posting_time")
        due_date = data.get("due_date") or posting_date
        
        item_rows = []
        taxes_rows = []

        for item in items:
            item_price = item.get("rate") or frappe.db.get_value("Item Price", {
                "item_code": item["item_code"],
                "selling": 1,
            }, "price_list_rate")

            row = {
                "item_code": item["item_code"],
                "qty": item.get("qty", 1),
                "rate": item_price
            }

            if item.get("item_tax_template"):
                row["item_tax_template"] = item["item_tax_template"]

            item_rows.append(row)

            if item.get("item_tax_template"):
                tax_details = frappe.db.sql("""
                    SELECT tax_type, tax_rate
                    FROM `tabItem Tax Template Detail`
                    WHERE parent=%s
                """, (item["item_tax_template"],), as_dict=True)

                for td in tax_details:
                    taxes_rows.append({
                        "charge_type": "On Net Total",
                        "account_head": td["tax_type"],
                        "rate": td["tax_rate"],
                        "description": f"Tax from {item['item_code']}",
                        "cost_center": data.get("cost_center")
                    })

        invoice = frappe.get_doc({
            "doctype": "Sales Invoice",
            "customer": customer,
            "posting_date": posting_date,
            "posting_time": posting_time,
            "set_posting_time": data.get("set_posting_time", 0),
            "due_date": due_date,
            "cost_center": data.get("cost_center"),
            "project": data.get("project"),
            "items": item_rows,
            "update_stock": data.get("update_stock", 0),
            "additional_discount_percentage": data.get("additional_discount_percentage", 0),
            "discount_amount": data.get("discount_amount", 0),
            "apply_discount_on": data.get("apply_discount_on"),
            "taxes_and_charges": data.get("taxes_and_charges"),
            "set_warehouse": data.get("warehouse"),
        })

        for tax in taxes_rows:
            invoice.append("taxes", tax)
   
        if data.get("taxes_and_charges"):
            tax_template = frappe.get_doc("Sales Taxes and Charges Template", data["taxes_and_charges"])
            for tax in tax_template.taxes:
                invoice.append("taxes", {
                    "charge_type": tax.charge_type,
                    "account_head": tax.account_head,
                    "description": tax.description,
                    "cost_center": tax.cost_center,
                    "rate": tax.rate,
                    "tax_amount": tax.tax_amount,
                    "included_in_print_rate": tax.included_in_print_rate,
                    "row_id": tax.row_id
                })


        invoice.run_method("calculate_taxes_and_totals")

        invoice.insert(ignore_permissions=True)

        return {
            "status": "success",
            "invoice_name": invoice.name
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Create Sales Invoice API")
        return {"status": "error", "message": str(e)}

@frappe.whitelist()
def get_sales_invoice_details(name):
    try:
        invoice = frappe.get_doc("Sales Invoice", name)

        return {
            "status": "success",
            "invoice": {
                "name": invoice.name,
                "status": invoice.status,
                "docstatus": invoice.docstatus,
                "company": invoice.company,
                "customer": invoice.customer,
                "customer_name" : invoice.customer_name,
                "posting_date": invoice.posting_date,
                "posting_time": invoice.posting_time,
                "set_posting_time": invoice.set_posting_time,
                "due_date": invoice.due_date,
                "cost_center": invoice.cost_center,
                "project": invoice.project,
                "warehouse": invoice.set_warehouse,
                "items": [
                    {
                        "item_code": i.item_code,
                        "item_name": i.item_name,
                        "qty": i.qty,
                        "rate": i.rate,
                        "warehouse": i.warehouse
                    } for i in invoice.items
                ],
                "update_stock": invoice.update_stock,
                "additional_discount_percentage": invoice.additional_discount_percentage,
                "discount_amount": invoice.discount_amount,
                "taxes_and_charges": invoice.taxes_and_charges,
                "total_taxes_and_charges": invoice.total_taxes_and_charges,
                "grand_total": invoice.grand_total
            }
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
    
@frappe.whitelist()
def get_all_sales_invoices(filters=None):
    try:
        invoices = frappe.get_all("Sales Invoice", fields=["name", "customer_name", "posting_date", "status"], order_by="creation desc", filters=filters)
        return {"status": "success", "invoices": invoices}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    
@frappe.whitelist()
def submit_sales_invoice(invoice_name):
    try:
        if not invoice_name:
            return {"status": "error", "message": "Invoice name is required."}

        invoice = frappe.get_doc("Sales Invoice", invoice_name)

        if invoice.docstatus == 1:
            return {"status": "error", "message": f"{invoice_name} is already submitted."}

        if invoice.docstatus == 2:
            return {"status": "error", "message": f"{invoice_name} is cancelled and cannot be submitted."}

        invoice.submit()

        return {"status": "success", "message": f"{invoice_name} submitted successfully."}

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Submit Sales Invoice API")
        return {"status": "error", "message": str(e)}
    
@frappe.whitelist()
def submit_payment_entry(payment_entry_name):
    try:
        if not payment_entry_name:
            return {"status": "error", "message": "Payment Entry name is required."}

        pe = frappe.get_doc("Payment Entry", payment_entry_name)

        if pe.docstatus == 1:
            return {"status": "error", "message": f"{payment_entry_name} is already submitted."}

        if pe.docstatus == 2:
            return {"status": "error", "message": f"{payment_entry_name} is cancelled and cannot be submitted."}

        pe.submit()

        return {"status": "success", "message": f"{payment_entry_name} submitted successfully."}

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Submit Payment Entry API")
        return {"status": "error", "message": str(e)}

@frappe.whitelist()
def get_all_material_requests(filters=None):
    try:
        return frappe.get_all("Material Request", fields=["name", "material_request_type", "transaction_date", "status", "docstatus"], order_by="creation desc", filters=filters)
    except Exception as e:
        log_error("Get All Material Requests Error", e)
        return {"error": str(e)}

@frappe.whitelist()
def get_material_request(name):
    try:
        doc = frappe.get_doc("Material Request", name)
        return doc.as_dict()
    except Exception as e:
        log_error("Get Material Request Error", e)
        return {"error": str(e)}
    
@frappe.whitelist()
def create_material_request(data):
    try:
        if isinstance(data, str):
            data = json.loads(data)

        doc = frappe.new_doc("Material Request")
        doc.material_request_type = data.get("material_request_type", "Purchase")
        doc.schedule_date = data.get("schedule_date")
        doc.set_warehouse = data.get("set_warehouse")
        doc.set_from_warehouse = data.get("set_from_warehouse") 
        doc.transaction_date = data.get("transaction_date")

        # Items list
        items = data.get("items", [])
        for item in items:
            doc.append("items", {
                "item_code": item["item_code"],
                "qty": item["qty"],
                "rate": item["rate"],
                "uom": item.get("stock_uom", "Nos")
            })

        doc.save(ignore_permissions=True)
       
        return {"status": "success","name": doc.name, "message": "Material Request saved as draft."}
    except Exception as e:
        log_error("Create Material Request Error", e)
        return {"error": str(e)}

@frappe.whitelist()
def submit_material_request(name):
    try:
        doc = frappe.get_doc("Material Request", name)
        if doc.docstatus == 0:
            doc.submit()
            return {"name": doc.name, "message": "Material Request submitted."}
        else:
            return {"error": "Material Request already submitted or cancelled."}
    except Exception as e:
        log_error("Submit Material Request Error", e)
        return {"error": str(e)}

@frappe.whitelist()
def get_sales_statistics():
    today = nowdate()
    month_start = get_first_day(today)
    year_start = f"{getdate(today).year}-01-01"

    stats = {}

    default_currency = frappe.db.get_single_value("Global Defaults", "default_currency")
    stats["currency"] = default_currency or ""

    # 1- Sales Invoice today (amount + count)
    stats["sales_today"] = frappe.db.sql("""
        SELECT 
            COALESCE(SUM(grand_total), 0) as total_amount,
            COUNT(name) as total_count
        FROM `tabSales Invoice`
        WHERE posting_date = %s AND docstatus = 1
    """, today, as_dict=True)[0]

    # 2- Sales Invoice this month
    stats["sales_month"] = frappe.db.sql("""
        SELECT 
            COALESCE(SUM(grand_total), 0) as total_amount,
            COUNT(name) as total_count
        FROM `tabSales Invoice`
        WHERE posting_date >= %s AND posting_date <= %s AND docstatus = 1
    """, (month_start, today), as_dict=True)[0]

    # 3- Sales Invoice this year
    stats["sales_year"] = frappe.db.sql("""
        SELECT 
            COALESCE(SUM(grand_total), 0) as total_amount,
            COUNT(name) as total_count
        FROM `tabSales Invoice`
        WHERE posting_date >= %s AND posting_date <= %s AND docstatus = 1
    """, (year_start, today), as_dict=True)[0]

    # 4- Payment Entries today grouped by Mode of Payment
    stats["payments_today"] = frappe.db.sql("""
        SELECT 
            mode_of_payment,
            COALESCE(SUM(paid_amount), 0) as total_amount,
            COUNT(name) as total_count
        FROM `tabPayment Entry`
        WHERE posting_date = %s AND docstatus = 1
        GROUP BY mode_of_payment
    """, today, as_dict=True)

    # 5- Overdue / Unpaid / Partly Paid invoices
    stats["invoice_status"] = frappe.db.sql("""
        SELECT 
            status,
            COUNT(name) as total_count,
            COALESCE(SUM(outstanding_amount), 0) as total_amount
        FROM `tabSales Invoice`
        WHERE status IN ('Overdue','Unpaid','Partly Paid') AND docstatus = 1
        GROUP BY status
    """, as_dict=True)

    # total overdue amount
    stats["total_overdue"] = frappe.db.sql("""
        SELECT COALESCE(SUM(outstanding_amount), 0) as total_amount
        FROM `tabSales Invoice`
        WHERE status IN ('Overdue','Unpaid','Partly Paid') AND docstatus = 1
    """, as_dict=True)[0]

    # 6- Sales Invoice Returns today
    stats["returns_today"] = frappe.db.sql("""
        SELECT 
            COALESCE(SUM(grand_total), 0) as total_amount,
            COUNT(name) as total_count
        FROM `tabSales Invoice`
        WHERE posting_date = %s AND is_return = 1 AND docstatus = 1
    """, today, as_dict=True)[0]

    # 7- Top 5 items sold today
    stats["top_items_today"] = frappe.db.sql("""
        SELECT 
            sii.item_code,
            sii.item_name,
            COALESCE(SUM(sii.qty), 0) as total_qty,
            COALESCE(SUM(sii.amount), 0) as total_income
        FROM `tabSales Invoice Item` sii
        JOIN `tabSales Invoice` si ON si.name = sii.parent
        WHERE si.posting_date = %s AND si.docstatus = 1
        GROUP BY sii.item_code, sii.item_name
        ORDER BY total_income DESC
        LIMIT 5
    """, today, as_dict=True)

    return stats