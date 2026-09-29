frappe.ui.form.on("KC Case", {
    refresh(frm) {
        if (frm.is_new() || frm.doc.sales_order) return;
        frm.add_custom_button(__("Create Sales Order"), () => {
            frappe.call({
                method: "kayanick_crm.case_api.make_sales_order",
                args: { case: frm.doc.name },
                freeze: true,
                callback: (r) => {
                    frm.reload_doc();
                    if (r.message) frappe.set_route("Form", "Sales Order", r.message);
                },
            });
        }).addClass("btn-primary");
    },
});
