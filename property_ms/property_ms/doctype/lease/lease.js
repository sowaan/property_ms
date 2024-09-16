// Copyright (c) 2023, Sowaan and contributors
// For license information, please see license.txt

frappe.ui.form.on("Lease", {
  refresh: function (frm) {
    if (frm.doc.docstatus == 1 && frm.doc.enabled == 1) {
      frm.add_custom_button(__("Terminate Lease"), function () {
        frappe.call({
          method: "property_ms.property_ms.doctype.lease.lease.terminate_lease",
          args: {
            doc: frm.doc,
          },
          freeze: true,
          callback: function (r) {
            frm.reload_doc();
          },
        });
      });
    }
  },

  property_type: function (frm) {
    if (frm.doc.property_type) {
      frm.set_query("property_name", function () {
        return {
          filters: [
            ["Properties", "property_type", "=", frm.doc.property_type],
          ],
        };
      });
    }
  },

  property_name: function (frm, cdt, cdn) {
    if (frm.doc.property_name) {
      // get units
      frm.set_value("choose_units", []);
      frappe.db
        .get_list("Unit", {
          filters: {
            property: frm.doc.property_name,
            rented: 0,
          },
          fields: ["*"],
        })
        .then((res) => {
          if (res.length == 0) {
            frappe.show_alert(
              {
                message: __("There are no free Units"),
                indicator: "red",
              },
              5
            );
          }
          for (let i = 0; i < res.length; i++) {
            const ele = res[i];
            var row = frappe.model.add_child(
              frm.doc,
              "Choose Units",
              "choose_units"
            );
            row.unit_name = ele.name;
            row.unit_number = ele.unit_number;
            row.rented = ele.rented;
          }
          refresh_field("choose_units");
        });

      // get owners
      frm.set_value("property_ownership", []);
      frappe.call({
        method: "frappe.client.get",
        args: {
          doctype: "Properties",
          name: frm.doc.property_name,
        },
        callback(r) {
          if (r.message) {
            var property = r.message;
            $.each(property.ownership, function (i, d) {
              var row = frappe.model.add_child(frm.doc, "Property Owner", "property_ownership");
              row.tenant = d.tenant;
              row.owner_name = d.owner_name;
              row.ownership = d.ownership;
              row.cost_center = d.cost_center;
            });
            refresh_field("property_ownership");
          }
        }
      });
    }
  },

  type: function (frm) {
    frm.trigger("payment_scheduling");
  },

  duration: function (frm) {
    frm.trigger("payment_scheduling");
  },

  payment_scheduling: function (frm) {
    if (frm.doc.duration && frm.doc.type) {
      frm.set_value("payments_scheduling", []);
      let len = 0;
      let totalMonthlyAmount = 0;
      let totalRate = 0;
      let Monthly = frm.doc.type == "Monthly";
      let Quarterly = frm.doc.type == "Quarterly";
      let HalfYearly = frm.doc.type == "Half Yearly";
      let Annually = frm.doc.type == "Annually";

      if (Monthly) {
        len = frm.doc.duration / 1;
      }
      if (Quarterly) {
        len = frm.doc.duration / 3;
      }
      if (HalfYearly) {
        len = frm.doc.duration / 6;
      }
      if (Annually) {
        len = frm.doc.duration / 12;
      }
      if (frm.doc.choose_units) {
        frm.doc.choose_units.forEach((unit) => {
          totalMonthlyAmount += unit.monthly;
        });
      }
      if (frm.doc.taxes) {
        frm.doc.taxes.forEach((tax) => {
          totalRate += tax.rate;
        });
      }
      if (len > 0) {
        if (frm.doc.increment_schedule.length > 0) {
          for (var l = 0; l < frm.doc.increment_schedule.length; l++) {
            var scheduleArray = frm.doc.increment_schedule[l];
            for (let i = 0; i < len; i++) {
              if ((i + 1) >= scheduleArray.from && (i + 1) <= scheduleArray.to) {
                var row = frappe.model.add_child(
                  frm.doc,
                  "Payments Scheduling",
                  "payments_scheduling"
                );
                var incrementAmount = totalMonthlyAmount * (scheduleArray.increment / 100);
                var amountAfterIncrement = totalMonthlyAmount + incrementAmount;

                if (Monthly) {
                  row.rent_amount = amountAfterIncrement;
                }
                if (Quarterly) {
                  row.rent_amount = amountAfterIncrement * 3;
                }
                if (HalfYearly) {
                  row.rent_amount = amountAfterIncrement * 6;
                }
                if (Annually) {
                  row.rent_amount = amountAfterIncrement * 12;
                }
                row.vat = totalRate;
                var add_pay_add =
                  frm.doc.ex_tax_on_add_char == 1 ? row.additional_charges : 0;
                var ext_pay_add =
                  frm.doc.ex_tax_on_add_char != 1 ? row.additional_charges : 0;
                var exc_insu_payment =
                  frm.doc.ex_ins_inv == 1 ? 0 : frm.doc.insur_payment;
                row.total_amount = row.rent_amount + ext_pay_add;
                row.total_tax = (row.total_amount / 100) * row.vat;
                row.total_amount = row.total_amount + row.total_tax + add_pay_add;
                row.additional_charges =
                  frm.doc.elec_payment +
                  frm.doc.maint_ser_pay +
                  frm.doc.wtr_payment +
                  exc_insu_payment;
              }
            }
          }
        } else {
          for (let i = 0; i < len; i++) {
            var row = frappe.model.add_child(
              frm.doc,
              "Payments Scheduling",
              "payments_scheduling"
            );
            if (Monthly) {
              row.rent_amount = totalMonthlyAmount;
            }
            if (Quarterly) {
              row.rent_amount = totalMonthlyAmount * 3;
            }
            if (HalfYearly) {
              row.rent_amount = totalMonthlyAmount * 6;
            }
            if (Annually) {
              row.rent_amount = totalMonthlyAmount * 12;
            }
            row.vat = totalRate;
            var add_pay_add =
              frm.doc.ex_tax_on_add_char == 1 ? row.additional_charges : 0;
            var ext_pay_add =
              frm.doc.ex_tax_on_add_char != 1 ? row.additional_charges : 0;
            var exc_insu_payment =
              frm.doc.ex_ins_inv == 1 ? 0 : frm.doc.insur_payment;
            row.total_amount = row.rent_amount + ext_pay_add;
            row.total_tax = (row.total_amount / 100) * row.vat;
            row.total_amount = row.total_amount + row.total_tax + add_pay_add;
            row.additional_charges =
              frm.doc.elec_payment +
              frm.doc.maint_ser_pay +
              frm.doc.wtr_payment +
              exc_insu_payment;
          }
        }
        frm.trigger("calculate");
      }
    }
  },

  taxes_and_charges: function (frm) {
    if (frm.doc.taxes_and_charges) {
      frm.set_value("taxes", []);
      frappe.call({
        method: "property_ms.property_ms.api.get_fee_sales_charges",
        args: {
          taxes_and_charges: frm.doc.taxes_and_charges,
        },
        callback: function (r) {
          if (r.message) {
            $.each(r.message, function (i, d) {
              var row = frappe.model.add_child(
                frm.doc,
                "Sales Taxes and Charges",
                "taxes"
              );
              row.charge_type = d.charge_type;
              row.account_head = d.account_head;
              row.rate = d.rate;
              row.included_in_print_rate = d.included_in_print_rate;
              row.base_total = d.base_total;
              row.cost_center = d.cost_center;
              row.description = d.description;
            });
          }
          refresh_field("taxes");
        },
      });
    }
  },

  ex_tax_on_add_char: function (frm) {
    if (frm.doc.ex_tax_on_add_char) {
      var row = frappe.model.add_child(
        frm.doc,
        "Sales Taxes and Charges",
        "taxes"
      );
      row.charge_type = "Actual";
      row.description = "Actual";
      row.rate = 0;
      frm.refresh_field("taxes");
    }
    if (frm.doc.ex_tax_on_add_char == 0) {
      frm.doc.taxes.pop();
      frm.refresh_field("taxes");
    }
    frm.trigger("payment_scheduling")
  },

  rent_start_date: function (frm) {
    frm.trigger("calculate");
  },

  grace_period: function (frm) {
    frm.trigger("calculate");
  },

  insur_payment: function (frm) {
    frm.trigger("calculate");
  },

  elec_payment: function (frm) {
    frm.trigger("calculate");
  },

  maint_ser_pay: function (frm) {
    frm.trigger("calculate");
  },

  wtr_payment: function (frm) {
    frm.trigger("calculate");
  },

  calculate: function (frm) {
    if (frm.doc.payments_scheduling.length > 0) {
      var exc_insu_payment =
        frm.doc.ex_ins_inv == 1 ? 0 : frm.doc.insur_payment;
      var total_ad_charg =
        frm.doc.elec_payment +
        frm.doc.maint_ser_pay +
        frm.doc.wtr_payment +
        exc_insu_payment;
      var graceDays = frm.doc.grace_period;
      // Convert start date to a moment object
      var rentDate = frm.doc.rent_start_date;
      var typeToDuration = {
        Monthly: 1,
        Quarterly: 3,
        "Half Yearly": 6,
        Annually: 12,
      };

      var mo_duration = typeToDuration[frm.doc.type] || 1;

      frm.doc.payments_scheduling.forEach((pay) => {
        pay.additional_charges = total_ad_charg;
        var add_pay_add =
          frm.doc.ex_tax_on_add_char == 1 ? pay.additional_charges : 0;
        var ext_pay_add =
          frm.doc.ex_tax_on_add_char != 1 ? pay.additional_charges : 0;
        pay.total_amount = pay.rent_amount + ext_pay_add;
        pay.total_tax = (pay.total_amount / 100) * pay.vat;
        pay.total_amount = pay.total_amount + pay.total_tax + add_pay_add;
        // Calculate due date by adding grace days and moving to the next month
        var dueDate = frappe.datetime.add_days(rentDate, graceDays);

        // Add the payment entry to the schedule
        pay.issued_date = rentDate;
        pay.due_date = dueDate;
        rentDate = frappe.datetime.add_months(rentDate, mo_duration);
      });
      frm.refresh_field("payments_scheduling");
    }
  },
});

frappe.ui.form.on("Choose Units", {
  choose_units_remove: function (frm) {
    frm.trigger("payment_scheduling");
  },
  choose_units_move: function (frm) {
    frm.trigger("payment_scheduling");
  },
  choose_units_add: function (frm) {
    frm.trigger("payment_scheduling");
  },

  yearly: function (frm, cdt, cdn) {
    frm.doc.choose_units.forEach((unit) => {
      unit.half_yearly = unit.yearly / 2;
      unit.monthly = unit.yearly / 12;
      unit.daily = unit.yearly / 365;
      unit.rented = 1;
    });
    refresh_field("choose_units");
    frm.trigger("payment_scheduling");
  },
});

frappe.ui.form.on("Increment Schedule", {
  increment_schedule_remove: function (frm) {
    frm.trigger("payment_scheduling");
  },
  increment_schedule_move: function (frm) {
    frm.trigger("payment_scheduling");
  },
  increment_schedule_add: function (frm) {
    frm.trigger("payment_scheduling");
  },
  from: function (frm) {
    frm.trigger("payment_scheduling");
  },
  to: function (frm) {
    frm.trigger("payment_scheduling");
  },
  increment: function (frm) {
    frm.trigger("payment_scheduling");
  },
});

frappe.ui.form.on("Payments Scheduling", {
  rent_amount: function (frm, cdt, cdn) {
    frm.trigger("additional_charges", cdt, cdn);
  },

  additional_charges: function (frm, cdt, cdn) {
    frm.doc.payments_scheduling.forEach((pay) => {
      var add_pay_add =
        frm.doc.ex_tax_on_add_char == 1 ? pay.additional_charges : 0;
      var ext_pay_add =
        frm.doc.ex_tax_on_add_char != 1 ? pay.additional_charges : 0;
      pay.total_amount = pay.rent_amount + ext_pay_add;
      pay.total_tax = (pay.total_amount / 100) * pay.vat;
      pay.total_amount = pay.total_amount + pay.total_tax + add_pay_add;
    });
    refresh_field("payments_scheduling");
  },
});

frappe.ui.form.on("Sales Taxes and Charges", {
  taxes_remove: function (frm, cdt, cdn) {
    frm.trigger("rate", cdt, cdn);
  },
  taxes_move: function (frm, cdt, cdn) {
    frm.trigger("rate", cdt, cdn);
  },
  taxes_add: function (frm, cdt, cdn) {
    frm.trigger("rate", cdt, cdn);
  },
  rate: function (frm, cdt, cdn) {
    let totalRate = 0;
    frm.doc.taxes.forEach((tax) => {
      totalRate += tax.rate;
    });
    frm.doc.payments_scheduling.forEach((pay) => {
      pay.vat = totalRate;
      var add_pay_add =
        frm.doc.ex_tax_on_add_char == 1 ? pay.additional_charges : 0;
      var ext_pay_add =
        frm.doc.ex_tax_on_add_char != 1 ? pay.additional_charges : 0;
      pay.total_amount = pay.rent_amount + ext_pay_add;
      pay.total_tax = (pay.total_amount / 100) * pay.vat;
      pay.total_amount = pay.total_amount + pay.total_tax + add_pay_add;
    });
    refresh_field("payments_scheduling");
  },
});
