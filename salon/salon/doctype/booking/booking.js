frappe.ui.form.on('Booking', {
    calculate_total: function(frm) {
        let total = 0;
        (frm.doc.table_services || []).forEach(row => {
            total += row.total_price || 0;
        });
        frm.set_value('total', total);
    },
    table_services_add: function(frm) {
        frm.trigger('calculate_total');
    },
    table_services_remove: function(frm) {
        frm.trigger('calculate_total');
    }
});

frappe.ui.form.on('Booking Items List', {
    service: function(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        if (row.service) {
            frappe.db.get_value('Service', row.service, 'price').then(r => {
                if (r.message && r.message.price) {
                    frappe.model.set_value(cdt, cdn, 'price', r.message.price);
                    frappe.model.set_value(cdt, cdn, 'total_price', (row.qty || 1) * r.message.price);
                    frm.trigger('calculate_total');
                }
            });
        }
    },
    qty: function(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        frappe.model.set_value(cdt, cdn, 'total_price', (row.qty || 0) * (row.price || 0));
        frm.trigger('calculate_total');
    },
    price: function(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        frappe.model.set_value(cdt, cdn, 'total_price', (row.qty || 0) * (row.price || 0));
        frm.trigger('calculate_total');
    }
});
