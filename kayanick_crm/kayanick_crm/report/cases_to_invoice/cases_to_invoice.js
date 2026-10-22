frappe.query_reports["Cases to Invoice"] = {
	filters: [
		{
			fieldname: "status",
			label: __("Status"),
			fieldtype: "Select",
			options: ["To Invoice", "Invoiced", "All"],
			default: "To Invoice",
		},
		{ fieldname: "invoice_type", label: __("Invoice Type"), fieldtype: "Select", options: ["", "System", "Cash"] },
		{ fieldname: "from_date", label: __("From Date"), fieldtype: "Date" },
		{ fieldname: "to_date", label: __("To Date"), fieldtype: "Date" },
	],
};
