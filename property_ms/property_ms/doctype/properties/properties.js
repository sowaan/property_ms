// Copyright (c) 2023, Sowaan and contributors
// For license information, please see license.txt

frappe.ui.form.on("Properties", {
  refresh: function (frm) {
    $(".leaflet-draw-draw-polyline").remove();
    $(".leaflet-draw-draw-polygon").remove();
    $(".leaflet-draw-draw-rectangle").remove();
    $(".leaflet-draw-draw-circlemarker").remove();

    frm.trigger('render_gallery');
  },
  property_images_add(frm) {
      frm.trigger('render_gallery');
  },
  property_images_remove(frm) {
      frm.trigger('render_gallery');
  },
  render_gallery(frm) {
      const wrapper = frm.fields_dict.image_gallery.$wrapper;
      wrapper.empty();

      const rows = frm.doc.property_images.filter(r => 
          !r.disabled //&& r.image && /\.(jpg|jpeg|png|gif|webp)$/i.test(r.image)
      );
      if (rows.length === 0) {
          wrapper.html('<p class="text-muted mt-2">No images uploaded.</p>');
          return;
      }

      // Extract image URLs
      const images = rows.map(r => ({
          low: r.image, // You can replace this with low-res URL if available
          full: r.image, // Full-res
          title: r.title || ''
      }));

      // Determine layout
      const count = images.length;
      let layoutClass = 'gallery-1';
      if (count === 2) layoutClass = 'gallery-2';
      else if (count === 3) layoutClass = 'gallery-3';
      else if (count >= 4) layoutClass = 'gallery-4';
      let html = `<style>
          .gallery-grid { display: grid; gap: 6px; }
          .gallery-grid img { width: 100%; height: 100%; object-fit: cover; border-radius: 6px; cursor: pointer; }
          .gallery-grid img:hover { opacity: 0.9; }
          .gallery-2 { grid-template-columns: 1fr 1fr; }
          .gallery-3 { grid-template-columns: 1fr 1.5fr; }
          .gallery-3 .left { display: grid; grid-template-rows: 1fr 1fr; gap: 6px; }
          .gallery-4 { grid-template-columns: 1fr 1.5fr; }
          .gallery-4 .left { display: grid; grid-template-columns: 1fr 1fr; grid-template-rows: 1fr 1fr; gap: 6px; }
          .gallery-more::after {
              content: attr(data-more);
              position: absolute; bottom: 0; right: 0;
              background: rgba(0,0,0,0.6); color: #fff;
              font-size: 16px; padding: 4px 10px;
              border-bottom-right-radius: 6px; border-top-left-radius: 6px;
          }
          @media(max-width:768px){ .gallery-2, .gallery-3, .gallery-4 { height:auto; grid-template-columns:1fr; } }
      </style>`;

      // Generate layout HTML
      if (count === 1) {
          html += `
              <div class="gallery-grid">
                  <img src="${images[0].low}" data-index="0" loading="lazy">
              </div>`;
      }
      else if (count === 2) {
          html += `
              <div class="gallery-grid gallery-2">
                  <img src="${images[0].low}" data-index="0" loading="lazy">
                  <img src="${images[1].low}" data-index="1" loading="lazy">
              </div>`;
      }
      else if (count === 3) {
          html += `
              <div class="gallery-grid gallery-3">
                  <div class="left">
                      <img src="${images[0].low}" data-index="0" loading="lazy">
                      <img src="${images[1].low}" data-index="1" loading="lazy">
                  </div>
                  <img src="${images[2].low}" data-index="2" loading="lazy">
              </div>`;
      }
      else if (count === 4) {
          html += `
              <div class="gallery-grid gallery-4">
                  <div class="left">
                      <img src="${images[0].low}" data-index="0" loading="lazy">
                      <img src="${images[1].low}" data-index="1" loading="lazy">
                      <img src="${images[2].low}" data-index="2" loading="lazy">
                      <img src="${images[3].low}" data-index="3" loading="lazy">
                  </div>
                  <img src="${images[3].low}" data-index="3" loading="lazy">
              </div>`;
      }
      else {
          // 5 or more
          const extra = count - 4;
          html += `
              <div class="gallery-grid gallery-4">
                  <div class="left">
                      <img src="${images[0].low}" data-index="0" loading="lazy">
                      <img src="${images[1].low}" data-index="1" loading="lazy">
                      <img src="${images[2].low}" data-index="2" loading="lazy">
                      <div style="position:relative;">
                          <img src="${images[3].low}" data-index="3" loading="lazy">
                          <div class="gallery-more" data-more="+${extra}"></div>
                      </div>
                  </div>
                  <img src="${images[4].low}" data-index="4" loading="lazy">
              </div>`;
      }

      wrapper.html(html);


      // LIGHTBOX
      
      // remove any previous click handlers before adding new ones
      wrapper.off('click', 'img');
      
      wrapper.on('click', 'img', function() {
          const startIndex = parseInt($(this).attr('data-index'));
          const dialog = new frappe.ui.Dialog({
              title: 'Image Viewer',
              size: 'extra-large',
              fields: [{ fieldtype: 'HTML', fieldname: 'lightbox_html' }],
              primary_action_label: 'Close',
              primary_action() { dialog.hide(); }
          });
          dialog.show();

          const buildLightbox = (i) => {
              const img = images[i];
              const content = `
                  <div style="position:relative;text-align:center;">
                      <img src="${img.full}" style="max-width:100%;max-height:80vh;border-radius:8px;">
                      <button id="prev-btn" style="position:absolute;top:50%;left:10px;transform:translateY(-50%);
                          background:#0008;color:white;border:none;border-radius:50%;width:36px;height:36px;cursor:pointer;">&#10094;</button>
                      <button id="next-btn" style="position:absolute;top:50%;right:10px;transform:translateY(-50%);
                          background:#0008;color:white;border:none;border-radius:50%;width:36px;height:36px;cursor:pointer;">&#10095;</button>
                  </div>`;
              dialog.fields_dict.lightbox_html.$wrapper.html(content);

              dialog.fields_dict.lightbox_html.$wrapper.find('#prev-btn').on('click', () => {
                  const prev = (i - 1 + images.length) % images.length;
                  buildLightbox(prev);
              });
              dialog.fields_dict.lightbox_html.$wrapper.find('#next-btn').on('click', () => {
                  const next = (i + 1) % images.length;
                  buildLightbox(next);
              });
          };

          buildLightbox(startIndex);
      });
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
