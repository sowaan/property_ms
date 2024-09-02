frappe.listview_settings["Lease"] = {
    add_fields: ["enabled"],
    get_indicator: function (doc) {
        if (doc.enabled == 0) {
            return [__("Terminated"), "red", "enabled,=,0"];
        } else {
            return [__("Scheduled"), "green", "enabled,=,1"];
        }
    },
};