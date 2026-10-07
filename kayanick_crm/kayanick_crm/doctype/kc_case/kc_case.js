
frappe.ui.form.on("KC Case", {
    setup(frm) {
        frm.set_query("item_code", "used_items", () => ({
            filters: { is_stock_item: 1, disabled: 0 }
        }));
    }
});
