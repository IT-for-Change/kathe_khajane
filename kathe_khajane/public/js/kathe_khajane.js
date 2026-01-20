frappe.ui.form.on('Story', {
    refresh(frm) {

        const field = frm.fields_dict.story_description;
        if (!field) return;

        const editor = field.$wrapper.find('.ql-editor');

        if (frm.doc.language === "Urdu") {
            editor.css({
                direction: 'rtl',
                'text-align': 'right',
                'unicode-bidi': 'embed'
            });
        } else {
            editor.css({
                direction: 'ltr',
                'text-align': 'left',
                'unicode-bidi': 'normal'
            });
        }
    }
});
