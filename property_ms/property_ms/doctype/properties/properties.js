// Copyright (c) 2023, Sowaan and contributors
// For license information, please see license.txt

frappe.ui.form.on("Properties", {
  refresh: function (frm) {
    $(".leaflet-draw-draw-polyline").remove();
    $(".leaflet-draw-draw-polygon").remove();
    $(".leaflet-draw-draw-rectangle").remove();
    $(".leaflet-draw-draw-circlemarker").remove();
  },
  map: function (frm) {
    var myMap = JSON.parse(frm.doc.map);
    if (myMap.features.length > 0) {
      if (
        myMap.features[0].geometry.type != "Polygon" &&
        myMap.features[0].geometry.type != "LineString"
      ) {
        var coords = myMap.features[0].geometry.coordinates;
        frm.set_value("longitude", coords[1]);
        frm.set_value("latitude", coords[0]);
      }
    }
  },
  property_province: function (frm) {
    if (frm.doc.property_province) {
      frm.set_query("property_city", function () {
        return {
          filters: [["City", "province", "=", frm.doc.property_province]],
        };
      });
    }
  },
  property_city: function (frm) {
    if (frm.doc.property_city) {
      frm.set_query("district", function () {
        return {
          filters: [["District", "city", "=", frm.doc.property_city]],
        };
      });
    }
  },
});
