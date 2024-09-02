import frappe
import json


@frappe.whitelist()
def get_fee_sales_charges(taxes_and_charges):
    if taxes_and_charges:
        stc = frappe.get_all(
            "Sales Taxes and Charges",
            fields=["*"],
            filters={"parent": taxes_and_charges},
            order_by="idx",
        )
        return stc
    
    
@frappe.whitelist()
def unrented(array):
    array = json.loads(array)
    for val in array:
        frappe.db.set_value("Unit", val.get("unit_name"), "rented", 0)
	
    return "Success"
