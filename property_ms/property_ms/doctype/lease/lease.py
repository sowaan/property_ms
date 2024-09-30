# Copyright (c) 2023, Sowaan and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import flt
from frappe.model.document import Document
import json



class Lease(Document):

	def validate(self):
		self.validate_increment_range()

	# Function to check for overlapping ranges and invalid range
	def validate_increment_range(self):
		for i, current in enumerate(self.increment_schedule, start=1):
			if i > 1:
				previous = self.increment_schedule[i-2]
				if current.get('from') <= previous.get('to'):
					frappe.throw(f"Error: Overlapping range detected between row {i-1} and row {i}")

	def on_submit(self):
		self.unit_rented()
		user_list = frappe.get_all("Has Role", filters={"role": "Property Approver"}, pluck="parent")
		if frappe.session.user not in user_list:
			for unit in self.choose_units:
				minimal_price = frappe.db.get_value("Unit", unit.unit_name, "minimal_rental_price")
				if unit.yearly < minimal_price:
					frappe.throw(f"Error: Rental price for unit {unit.unit_name} is below minimal rental price")




		# for payment in self.payments_scheduling:
		# 	rate_wo_tax = flt(payment.total_amount) - flt(payment.total_tax)
		# 	rate = rate_wo_tax if self.ex_tax_on_add_char == 0 else rate_wo_tax - payment.additional_charges
		# 	if self.ex_tax_on_add_char == 1:
		# 		for item in self.taxes:
		# 			if item.charge_type == "Actual":
		# 				item.tax_amount = payment.additional_charges
		# 				item.rate = 0
			
		# 	invoice = frappe.get_doc({
		# 		"doctype": "Sales Invoice",
		# 		"customer": self.renter,
		# 		"posting_date": payment.issued_date,
		# 		"due_date": payment.due_date,
		# 		"taxes_and_charges": self.taxes_and_charges,
		# 		"taxes": self.taxes,
		# 		"company": self.company,
		# 		"custom_lease_reference": self.name,
		# 	})

		# 	for tenant in self.property_ownership:
		# 		invoice.append("items", {
		# 			"item_code": self.item,
		# 			"qty": 1,
		# 			"rate": rate * (tenant.ownership / 100),
		# 			"cost_center": tenant.cost_center,	
		# 		})
		# 	invoice.save()
			# invoice.submit()

	def unit_rented(self):
		for unit in self.choose_units:
			frappe.db.set_value("Unit", unit.unit_name, "rented", 1)

	def on_cancel(self):
		for unit in self.choose_units:
			frappe.db.set_value("Unit", unit.unit_name, "rented", 0)

@frappe.whitelist()
def terminate_lease(doc):
	doc = json.loads(doc)
	frappe.db.set_value("Lease", doc.get('name'), "enabled", 0)
	for unit in doc.get('choose_units'):
		frappe.db.set_value("Unit", unit.get('unit_name'), "rented", 0)
	frappe.msgprint("Lease has been terminated successfully")


@frappe.whitelist()
def make_sales_invoice_scheduler():
	lease_list = frappe.get_all("Lease", filters=[['enabled', '=', 1], ['docstatus', '!=', 2]])

	for lease in lease_list:
		doc = frappe.get_doc('Lease', lease.name)
		for payment in doc.payments_scheduling:
			if str(payment.issued_date) <= frappe.utils.nowdate() and payment.invoiced == 0:
				frappe.db.set_value("Payments Scheduling", payment.name, 'invoiced', 1)
				rate_wo_tax = flt(payment.total_amount) - flt(payment.total_tax)
				rate = rate_wo_tax if doc.ex_tax_on_add_char == 0 else rate_wo_tax - payment.additional_charges
				if doc.ex_tax_on_add_char == 1:
					for item in doc.taxes:
						if item.charge_type == "Actual":
							item.tax_amount = payment.additional_charges
							item.rate = 0
				
				invoice = frappe.get_doc({
					"doctype": "Sales Invoice",
					"customer": doc.renter,
					"set_posting_time": 1,
					"posting_date": payment.issued_date,
					"due_date": payment.due_date,
					"taxes_and_charges": doc.taxes_and_charges,
					"taxes": doc.taxes,
					"company": doc.company,
					"custom_lease_reference": doc.name,
				})

				for tenant in doc.property_ownership:
					invoice.append("items", {
						"item_code": doc.item,
						"qty": 1,
						"rate": rate * (tenant.ownership / 100),
						"cost_center": tenant.cost_center,	
					})
				invoice.save()

