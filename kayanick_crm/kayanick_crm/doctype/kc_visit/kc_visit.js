frappe.ui.form.on("KC Visit", {
    setup(frm) {
        frm.set_query("doctor", () => ({
            filters: frm.doc.hospital_account ? { hospital_account: frm.doc.hospital_account } : {},
        }));
    },
    hospital_account(frm) {
        frm.set_value("doctor", "");
    },
    onload(frm) {
        if (frm.is_new() && navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                (pos) => {
                    const gj = {
                        type: "FeatureCollection",
                        features: [{
                            type: "Feature",
                            properties: { point_type: "circle", radius: pos.coords.accuracy || 10 },
                            geometry: { type: "Point", coordinates: [pos.coords.longitude, pos.coords.latitude] },
                        }],
                    };
                    frm.set_value("geolocation", JSON.stringify(gj));
                    frm.set_value("check_in_time", frappe.datetime.now_datetime());
                },
                (err) => console.warn("Geolocation unavailable:", err.message),
                { enableHighAccuracy: true, timeout: 10000 }
            );
        }
    },
});
