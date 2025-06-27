# Copyright (c) 2023, Sowaan and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import flt, nowdate
from frappe.model.document import Document
import json
from erpnext.stock.get_item_details import _get_item_tax_template
from erpnext.controllers.taxes_and_totals import get_itemised_tax


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


# @frappe.whitelist()
# def make_sales_invoice_scheduler():
# 	try:
# 		lease_list = frappe.get_all("Lease", filters=[['enabled', '=', 1], ['docstatus', '=', 1]])
# 		for lease in lease_list:
# 			try:
# 				total_unit_amount = 0
# 				doc = frappe.get_doc('Lease', lease.name)
# 				total_unit_amount += sum(unit.yearly for unit in doc.choose_units)
# 				for payment in doc.payments_scheduling:
# 					try:
# 						additional_charges = payment.additional_charges / len(doc.choose_units)
# 						if str(payment.issued_date) <= nowdate() and payment.invoiced == 0:
# 							frappe.db.set_value("Payments Scheduling", payment.name, 'invoiced', 1)
# 							# rate_wo_tax = flt(payment.total_amount) - flt(payment.total_tax)
							
# 							for tenant in doc.property_ownership:
# 								try:
# 									invoice = frappe.get_doc({
# 										"doctype": "Sales Invoice",
# 										"customer": doc.renter,
# 										"set_posting_time": 1,
# 										"posting_date": payment.issued_date,
# 										"due_date": payment.due_date,
# 										"company": doc.company,
# 										"custom_lease_reference": doc.name
# 									})

# 									for unit in doc.choose_units:
# 										itemRate = 0
# 										if not doc.ex_tax_on_add_char:
# 											itemRate = ((unit.yearly / total_unit_amount) * (payment.rent_amount + payment.additional_charges)) # total_amount <-- rent_amount + additional_charges 
# 										else:
# 											itemRate = ((unit.yearly / total_unit_amount) * payment.rent_amount)

# 										invoice.append("items", {
# 											"item_code": doc.item,
# 											"qty": 1,
# 											"rate": itemRate * (tenant.ownership / 100),
# 											"cost_center": tenant.cost_center,	
# 											"properties": doc.property_name,
# 											"unit_center": unit.unit_name,
# 											# "income_account": income_account.name	
# 										})


# 										if doc.ex_tax_on_add_char:
# 											if additional_charges > 0:
# 												additional_charges_item = get_additional_item()
# 												invoice.append("items", {
# 													"item_code": additional_charges_item.item_code,
# 													"qty": 1,
# 													"rate": additional_charges * (tenant.ownership / 100),
# 													"cost_center": tenant.cost_center,
# 													"properties": doc.property_name,
# 													"unit_center": unit.unit_name,
# 												})
# 											for lease_tax in doc.taxes:
# 												itemRate = 0
# 												for item in invoice.items:
# 													if item.item_code == doc.item:
# 														itemRate = item.rate

# 												tax_amount = (itemRate / 100) * lease_tax.rate
# 												if tax_amount > 0:
# 													invoice.append("taxes", {
# 														"charge_type": "Actual",
# 														"account_head": lease_tax.account_head,
# 														"rate": lease_tax.rate,
# 														"description": lease_tax.description,
# 														"cost_center": lease_tax.cost_center,
# 														"tax_amount": tax_amount
# 													})
# 										else:
# 											invoice.taxes_and_charges = doc.taxes_and_charges
# 											for lease_tax in doc.taxes:
# 												invoice.append("taxes", {
# 													"charge_type": lease_tax.charge_type,
# 													"account_head": lease_tax.account_head,
# 													"rate": lease_tax.rate,
# 													"description": lease_tax.description,
# 													"cost_center": lease_tax.cost_center,
# 													# "tax_amount": (itemRate / 100) * lease_tax.rate,
# 												})
# 									invoice.set_missing_values()
# 									invoice.calculate_taxes_and_totals()
# 									invoice.insert()
# 								except Exception as tenant_err:
# 									frappe.log_error(f"Error creating invoice for tenant in lease {lease.name}: {str(tenant_err)}")
# 					except Exception as payment_err:
# 						frappe.log_error(f"Error processing payment schedule for lease {lease.name}: {str(payment_err)}")
# 			except Exception as lease_err:
# 				frappe.log_error(f"Error processing lease {lease.name}: {str(lease_err)}")
# 	except Exception as e:
# 		frappe.log_error(f"Unexpected error in make_sales_invoice_scheduler: {str(e)}")


@frappe.whitelist()
def make_sales_invoice_scheduler():
	try:
		lease_list = frappe.get_all("Lease", filters=[['enabled', '=', 1], ['docstatus', '=', 1]])
		for lease in lease_list:
			try:
				check = "start"
				total_unit_amount = 0
				doc = frappe.get_doc('Lease', lease.name)
				total_unit_amount += sum(unit.yearly for unit in doc.choose_units)

				additional_item = get_additional_item()
				additional_item_code = additional_item.item_code
				zero_tax_acc = None
				zero_tax_acc_si_tax = None
				# rent_vat_acc = doc.taxes[0].account_head if doc.taxes else None
				tax_rate = doc.taxes[0].rate if doc.taxes else 0
				rent_result = frappe.db.sql("""
										SELECT ittd.parent
										FROM `tabItem Tax Template Detail` ittd
										JOIN `tabItem Tax Template` itt ON itt.name = ittd.parent
										WHERE ittd.parenttype = 'Item Tax Template'
											AND ittd.tax_rate = %s
											AND itt.company = %s
										LIMIT 1
									""", (tax_rate, doc.company), as_dict=True)
				rent_vat_acc = rent_result[0]["parent"] if rent_result else None
				currency = frappe.db.get_value('Company', doc.company, 'default_currency')
				charge_type = doc.taxes[0].charge_type if doc.taxes else "On Net Total"
				for payment in doc.payments_scheduling:
					try:
						additional_charges = payment.additional_charges / len(doc.choose_units)
						if str(payment.issued_date) <= nowdate() and payment.invoiced == 0:
							frappe.db.set_value("Payments Scheduling", payment.name, 'invoiced', 1)

							for tenant in doc.property_ownership:
								try:
									invoice = frappe.new_doc("Sales Invoice")
									invoice.customer = doc.renter
									invoice.set_posting_time = 1
									invoice.posting_date = payment.issued_date
									invoice.due_date = payment.due_date
									invoice.company = doc.company
									invoice.custom_lease_reference = doc.name
									invoice.disable_rounded_total = 0

									for unit in doc.choose_units:
										itemRate = 0
										if not doc.ex_tax_on_add_char:
											itemRate = ((unit.yearly / total_unit_amount) * (payment.rent_amount + payment.additional_charges))
										else:
											itemRate = ((unit.yearly / total_unit_amount) * payment.rent_amount)
										result = frappe.db.sql("""
											SELECT
								 				ittd.parent
								 								
											FROM `tabItem Tax Template Detail` ittd
											JOIN `tabItem Tax Template` itt ON itt.name = ittd.parent
											WHERE ittd.parenttype = 'Item Tax Template'
												AND ittd.tax_rate = %s
												AND itt.company = %s
											LIMIT 1
										""", (0, doc.company), as_dict=True)
										if doc.expenses and doc.expenses[0].item_tax_template:
											zero_tax_acc = doc.expenses[0].item_tax_template
										elif result:
											zero_tax_acc = result[0]["parent"]
										if zero_tax_acc:
											acc_doc = frappe.get_doc("Item Tax Template", zero_tax_acc)
											if acc_doc and acc_doc.taxes:
												zero_tax_acc_si_tax = acc_doc.taxes[0].tax_type if acc_doc.taxes else None
										
											

										rent_item = {
											"item_code": doc.item,
											"qty": 1,
											"rate": itemRate * (tenant.ownership / 100),
											"cost_center": tenant.cost_center,
											"properties": doc.property_name,
											"unit_center": unit.unit_name
										}

										if rent_vat_acc:
											rent_item["item_tax_template"] = rent_vat_acc

										invoice.append("items", rent_item)


										if doc.ex_tax_on_add_char:
											if additional_charges > 0:
												add_item = {
													"item_code": additional_item_code,
													"qty": 1,
													"rate": additional_charges * (tenant.ownership / 100),
													"cost_center": tenant.cost_center,
													"properties": doc.property_name,
													"unit_center": unit.unit_name
												}

												if zero_tax_acc:
													add_item["item_tax_template"] = zero_tax_acc
												invoice.append("items", add_item)
									try:
										invoice.set_missing_values()
										invoice.flags.ignore_permissions = True
										invoice.set("taxes", [])

										exis_temp = []

										for item in invoice.items:
											if not item.item_tax_template or item.item_tax_template in exis_temp:
												continue
											template = frappe.get_doc("Item Tax Template", item.item_tax_template)
											exis_temp.append(item.item_tax_template)

											for tax_row in template.taxes:
												invoice.append("taxes", {
													"charge_type": charge_type,
													"account_head": tax_row.tax_type,
													# "rate": tax_row.tax_rate,
													"rate": 0,
													"description": tax_row.tax_type,
													"cost_center": doc.taxes[0].cost_center or item.cost_center or invoice.company_default_cost_center,
													"account_currency": currency,
													"tax_amount": payment.total_tax if tax_row.tax_rate and tax_row.tax_rate != 0 else 0
												})

										
										invoice.calculate_taxes_and_totals()
										invoice.insert()
										# invoice.save()
									except Exception as e:
										frappe.log_error(f"Validation error while creating invoice for tenant in lease {lease.name}: {str(e)}")
										# print(f"[ERROR] Validation error while creating invoice for tenant in lease {lease.name}: {str(ve)}")
									
								except Exception as tenant_err:
									frappe.log_error(f"Error creating invoice for tenant in lease {lease.name}: {str(tenant_err)}")
									# print(f"[ERROR] Creating invoice for tenant in lease {lease.name}: {str(tenant_err)}")

					except Exception as payment_err:
						frappe.log_error(f"Error processing payment schedule for lease {lease.name}: {str(payment_err)}")
						# print(f"[ERROR] Processing payment schedule for lease {lease.name}: {str(payment_err)}")
			except Exception as lease_err:
				frappe.log_error(f"Error processing lease {lease.name}: {str(lease_err)}")
				# print(f"[ERROR] Processing lease {lease.name}: {str(lease_err)}")

	except Exception as e:
		frappe.log_error(f"Unexpected error in make_sales_invoice_scheduler: {str(e)}")
		# print(f"[ERROR] Unexpected error in make_sales_invoice_scheduler: {str(e)}")



@frappe.whitelist()
def get_additional_item():
	if not frappe.db.exists("Item", {
		"additional_charges_item": 1
	}):
		return frappe.get_last_doc("Item")
	else:
		return frappe.get_last_doc("Item", {
			"additional_charges_item": 1
		})

