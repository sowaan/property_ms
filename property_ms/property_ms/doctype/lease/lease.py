# Copyright (c) 2023, Sowaan and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import flt
from frappe.model.document import Document
import json



class Lease(Document):
	def validate(self):
		self.validate_increment_range()
		# make_sales_invoice_scheduler()

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


	def unit_rented(self):
		for unit in self.choose_units:
			frappe.db.set_value("Unit", unit.unit_name, "rented", 1)

	def on_cancel(self):
		for unit in self.choose_units:
			frappe.db.set_value("Unit", unit.unit_name, "rented", 0)

@frappe.whitelist()
def terminate_lease(doc, terminated_date):
	doc = json.loads(doc)
	frappe.db.set_value("Lease", doc.get('name'), "enabled", 0)
	frappe.db.set_value("Lease", doc.get('name'), "terminated_date", terminated_date)
	for unit in doc.get('choose_units'):
		frappe.db.set_value("Unit", unit.get('unit_name'), "rented", 0)
	frappe.msgprint("Lease has been terminated successfully")


@frappe.whitelist()
def make_sales_invoice_scheduler():
	# print("Scheduler started \n\n\n")
	lease_list = frappe.get_all("Lease", filters=[['enabled', '=', 1], ['docstatus', '=', 1]])

	for lease in lease_list:
		doc = frappe.get_doc('Lease', lease.name)
		for payment in doc.payments_scheduling:
			additional_charges = payment.additional_charges / len(doc.choose_units)
			if str(payment.issued_date) <= frappe.utils.nowdate() and payment.invoiced == 0:
				frappe.db.set_value("Payments Scheduling", payment.name, 'invoiced', 1)
				rate_wo_tax = flt(payment.total_amount) - flt(payment.total_tax)
				# if doc.ex_tax_on_add_char == 1:
				# 	for item in doc.taxes:
				# 		if item.charge_type == "Actual":
				# 			# item.tax_amount = payment.additional_charges
				# 			item.rate = 0
				
				for tenant in doc.property_ownership:
					invoice = frappe.get_doc({
						"doctype": "Sales Invoice",
						"customer": doc.renter,
						"set_posting_time": 1,
						"posting_date": payment.issued_date,
						"due_date": payment.due_date,
						# "taxes_and_charges": doc.taxes_and_charges,
						"company": doc.company,
						"custom_lease_reference": doc.name,
					})

					for unit in doc.choose_units:
						itemRate = 0
						if doc.ex_tax_on_add_char == 0:
							itemRate = payment.rent_amount + additional_charges
							# if doc.type == "Monthly":
							# 	itemRate = unit.monthly + additional_charges
							# elif doc.type == "Quarterly":
							# 	itemRate = (unit.monthly * 3) + additional_charges
							# elif doc.type == "Half Yearly":
							# 	itemRate = unit.half_yearly + additional_charges
							# elif doc.type == "Yearly":
							# 	itemRate = unit.yearly + additional_charges
						else:
							itemRate = payment.rent_amount
							# if doc.type == "Monthly":
							# 	itemRate = unit.monthly
							# elif doc.type == "Quarterly":
							# 	itemRate = (unit.monthly * 3)
							# elif doc.type == "Half Yearly":
							# 	itemRate = unit.half_yearly
							# elif doc.type == "Yearly":
							# 	itemRate = unit.yearly

						# income_account = frappe.get_last_doc("Account", {
						# 	"company": doc.company,
						# 	"account_type": "Income Account",
						# 	"disabled": 0
						# })

						invoice.append("items", {
							"item_code": doc.item,
							"qty": 1,
							"rate": itemRate * (tenant.ownership / 100),
							"cost_center": tenant.cost_center,	
							"properties": doc.property_name,
							"unit_center": unit.unit_name,
							# "income_account": income_account.name	
						})

						if doc.ex_tax_on_add_char == 1:

							additional_charges_item = get_additional_item()
							invoice.append("items", {
								"item_code": additional_charges_item.item_code,
								"qty": 1,
								"rate": additional_charges * (tenant.ownership / 100),
								"cost_center": tenant.cost_center,
								"properties": doc.property_name,
								"unit_center": unit.unit_name,
								# "income_account": income_account.name
							})

							for lease_tax in doc.taxes:
								itemRate = 0
								for item in invoice.items:
									if item.item_code == doc.item:
										itemRate = item.rate

								# print((itemRate / 100) * lease_tax.rate, "Tax Amount \n\n\n")
								invoice.append("taxes", {
									"charge_type": "Actual",
									"account_head": lease_tax.account_head,
									"rate": lease_tax.rate,
									"description": lease_tax.description,
									"cost_center": lease_tax.cost_center,
									"tax_amount": (itemRate / 100) * lease_tax.rate,
								})
						# for add_charge in doc.expenses:
						# 	invoice.append("items", {
						# 		"item_code": add_charge.expense_type,
						# 		"qty": 1,
						# 		"rate": add_charge.expence_amount * (tenant.ownership / 100),
						# 		"cost_center": tenant.cost_center,
						# 		"properties": doc.property_name,
						# 		"unit_center": unit.unit_name,
						# 		"item_tax_template": add_charge.item_tax_template
						# 	})
					# invoice.run_method("set_missing_values")
					# invoice.run_method("calculate_taxes_and_totals")
					invoice.set_missing_values()
					invoice.calculate_taxes_and_totals()
					# print(invoice, "Invoice Values \n\n\n")
					invoice.insert()


@frappe.whitelist()
def get_additional_item():
	return frappe.get_last_doc("Item", {
		"additional_charges_item": 1
	})

