// Copyright (c) 2023, Sowaan and contributors
// For license information, please see license.txt

frappe.ui.form.on("Unit", {
	refresh(frm) {
        render_gallery(frm);
	},
    unit_images_add(frm) {
        render_gallery(frm);
    },
    unit_images_remove(frm) {
        render_gallery(frm);
    },
    unit_images_on_form_rendered(frm) {
        render_gallery(frm);
    },
});


function render_gallery(frm) {
    const wrapper = frm.fields_dict.image_gallery.$wrapper;
    wrapper.empty();

    const rows = frm.doc.unit_images?.filter(r => !r.disabled && r.image) || [];
    if (rows.length === 0) {
        wrapper.html('<p class="text-muted mt-2">No images uploaded.</p>');
        return;
    }

    const galleryId = `pswp-gallery-${frm.doc.name}`;
    const total = rows.length;
    const layoutClass = total === 1 ? 'one'
                        : total === 2 ? 'two'
                        : total === 3 ? 'three'
                        : total === 4 ? 'four'
                        : 'more';

    let html = `<div id="${galleryId}" class="pswp-gallery ${layoutClass}">`;

    rows.forEach((r, i) => {
        const image_url = frappe.urllib.get_full_url(r.image);
        const title = frappe.utils.escape_html(r.title || '');

        // For more than 4 images, show only first 4 thumbnails and overlay on last
        if (i < 4) {
            html += `
                <div class="image-box">
                    <a href="${image_url}" 
                      data-pswp-width="1600"
                      data-pswp-height="900"
                      data-pswp-caption="${title}">
                        <img src="${image_url}" alt="${title}"/>
                        ${i === 3 && total > 4 ? `<div class="overlay" data-open-gallery="true">+${total - 4}</div>` : ''}
                    </a>
                </div>
            `;
        } else {
            // Hidden extra images for lightbox
            html += `
                <a href="${image_url}" 
                   data-pswp-width="1600"
                   data-pswp-height="900"
                   data-pswp-caption="${title}" 
                   style="display:none;"></a>
            `;
        }
    });

    html += `</div>`;
    wrapper.html(html);

    // allow "+X" overlay to open the lightbox
    wrapper.find('.overlay[data-open-gallery]').on('click', function(e) {
        e.preventDefault();
        wrapper.find('a')[3]?.click(); // trigger click on 4th image
    });


    load_photoswipe(galleryId);
}

function load_photoswipe(galleryId) {
    
    if (window.PhotoSwipeLightbox) {
        init_photoswipe(galleryId);
        return;
    }

    frappe.require([
        '/assets/property_ms/photoswipe/photoswipe.umd.min.js',
        '/assets/property_ms/photoswipe/photoswipe-lightbox.umd.min.js',
        '/assets/property_ms/photoswipe/photoswipe.css'
    ], () => {
        init_photoswipe(galleryId);
    });
}

function init_photoswipe(galleryId) {
    const gallerySelector = document.getElementById(galleryId);
    if (!gallerySelector) return;

    const lightbox = new PhotoSwipeLightbox({
        gallery: gallerySelector,
        children: 'a',
        pswpModule: PhotoSwipe,
        errorMsg: 'The photo cannot be loaded'
    });

    // Add zoom & fullscreen buttons
    lightbox.on('uiRegister', function() {
        lightbox.pswp.ui.registerElement({
            name: 'fullscreen',
            ariaLabel: 'Fullscreen',
            order: 9,
            isButton: true,
            html: '⛶',
            onClick: () => {
                const pswp = lightbox.pswp;
                if (!document.fullscreenElement) pswp.element.requestFullscreen();
                else document.exitFullscreen();
            }
        });
    });

    lightbox.init();
}
