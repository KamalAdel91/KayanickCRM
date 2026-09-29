frappe.ui.form.on("KC Visit", {
    setup(frm) {
        frm.set_query("doctor", () => ({
            filters: frm.doc.hospital ? { hospital: frm.doc.hospital } : {},
        }));
    },
    hospital(frm) {
        frm.set_value("doctor", "");
    },
    onload(frm) {
        if (!frm.is_new()) return;
        frm.set_value("check_in_time", frappe.datetime.now_datetime());
        if (!navigator.geolocation) return;
        navigator.geolocation.getCurrentPosition(
            (pos) => {
                frm.set_value("geolocation", JSON.stringify({
                    type: "FeatureCollection",
                    features: [{
                        type: "Feature",
                        properties: { point_type: "circle", radius: pos.coords.accuracy || 10 },
                        geometry: { type: "Point", coordinates: [pos.coords.longitude, pos.coords.latitude] },
                    }],
                }));
            },
            (err) => console.warn("Geolocation unavailable:", err.message),
            { enableHighAccuracy: true, timeout: 10000 }
        );
    },
});
