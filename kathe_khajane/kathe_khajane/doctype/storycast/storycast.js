// Copyright (c) 2026, kkadmin and contributors
// For license information, please see license.txt

frappe.ui.form.on('Storycast', {
    refresh: function(frm) {

        if (!frm.is_new()) {

            frm.add_custom_button('Open Podcast Feed', function() {

                const feed_url =
                    window.location.origin +
                    "/api/method/kathe_khajane.podcast.generate?docname=" +
                    frm.doc.name;

                window.open(feed_url, "_blank");

            }, __('Podcast'));

        }
    }
});