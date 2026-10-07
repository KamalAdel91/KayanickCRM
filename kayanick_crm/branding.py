"""App icons and manifest built from the company logo (Company > Company Logo).

Served from the site root:
  /kayanick-manifest.json   web app manifest
  /kayanick-icon-192.png    /kayanick-icon-512.png   app / notification icons (logo on white, padded)
  /kayanick-badge.png       white silhouette for the Android status bar
Falls back to the bundled icons when no company has a logo."""
import io
import json

import frappe
from frappe.website.page_renderers.base_renderer import BaseRenderer
from werkzeug.wrappers import Response

ICON_SIZES = {"kayanick-icon-192.png": 192, "kayanick-icon-512.png": 512}
FALLBACK = "icon-{0}.png"  # in public/frontend


def company_logo():
    company = frappe.defaults.get_global_default("company")
    logo = frappe.db.get_value("Company", company, "company_logo") if company else None
    if not logo:
        logo = frappe.db.get_value("Company", {"company_logo": ["is", "set"]}, "company_logo")
    return logo


def _logo_image():
    from PIL import Image

    url = company_logo()
    if not url:
        return None
    try:
        content = frappe.get_doc("File", {"file_url": url}).get_content()
        return Image.open(io.BytesIO(content)).convert("RGBA")
    except Exception:
        frappe.log_error(title="Kayanick CRM: could not read the company logo")
        return None


def _png(img):
    buf = io.BytesIO()
    img.save(buf, "PNG", optimize=True)
    return buf.getvalue()


def _icon(size):
    from PIL import Image

    logo = _logo_image()
    if logo is None:
        # "public" as its own part: Frappe would otherwise turn icon-192 into icon_192
        with open(frappe.get_app_path("kayanick_crm", "public", "frontend", FALLBACK.format(192 if size <= 192 else 512)), "rb") as f:
            return f.read()
    logo.thumbnail((int(size * 0.72), int(size * 0.72)), Image.LANCZOS)  # keep inside the maskable safe zone
    canvas = Image.new("RGBA", (size, size), (255, 255, 255, 255))
    canvas.alpha_composite(logo, ((size - logo.width) // 2, (size - logo.height) // 2))
    return _png(canvas.convert("RGB"))


def _badge():
    """White shape on transparent: from the logo's transparency, or its non-white pixels."""
    from PIL import Image, ImageChops

    size = 96
    logo = _logo_image()
    if logo is None:
        return None
    alpha = logo.getchannel("A")
    if alpha.getextrema()[0] == 255:  # no transparency: treat near-white as background
        gray = logo.convert("L")
        alpha = gray.point(lambda v: 255 if v < 200 else 0)
    bbox = alpha.getbbox()
    if bbox:
        alpha = alpha.crop(bbox)
    alpha.thumbnail((int(size * 0.8), int(size * 0.8)), Image.LANCZOS)
    mask = Image.new("L", (size, size), 0)
    mask.paste(alpha, ((size - alpha.width) // 2, (size - alpha.height) // 2))
    out = Image.new("RGBA", (size, size), (255, 255, 255, 0))
    out.putalpha(ImageChops.multiply(mask, Image.new("L", (size, size), 255)))
    return _png(out)


def manifest():
    return {
        "id": "/KayanickCRM",
        "name": "Kayanick CRM",
        "short_name": "Kayanick CRM",
        "start_url": "/KayanickCRM",
        "scope": "/KayanickCRM",
        "display": "standalone",
        "background_color": "#f9fafb",
        "theme_color": "#1f55e6",
        "icons": [
            {"src": "/kayanick-icon-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any"},
            {"src": "/kayanick-icon-192.png", "sizes": "192x192", "type": "image/png", "purpose": "maskable"},
            {"src": "/kayanick-icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any"},
            {"src": "/kayanick-icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"},
        ],
    }


def _cached(key, build):
    """Cached per logo, so a new logo shows up without a deploy."""
    ck = "kc_brand:{0}:{1}".format(key, company_logo() or "-")
    data = frappe.cache.get_value(ck)
    if data is None:
        data = build()
        frappe.cache.set_value(ck, data, expires_in_sec=6 * 3600)
    return data


class BrandingRenderer(BaseRenderer):
    PATHS = ("kayanick-manifest.json", "kayanick-badge.png", *ICON_SIZES)

    def can_render(self):
        return self.path.strip("/") in self.PATHS

    def render(self):
        path = self.path.strip("/")
        if path == "kayanick-manifest.json":
            r = Response(json.dumps(manifest()), mimetype="application/manifest+json")
        elif path == "kayanick-badge.png":
            data = _cached("badge", _badge)
            if not data:
                return Response(status=404)
            r = Response(data, mimetype="image/png")
        else:
            r = Response(_cached(path, lambda: _icon(ICON_SIZES[path])), mimetype="image/png")
        r.headers["Cache-Control"] = "public, max-age=3600"
        return r
