"""Invoice PDFs failed ("ProtocolUnknownError") on every print format: the Letter Head loads its fonts with
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@600;700;800...'), and when Frappe cuts the
header out for wkhtmltopdf the URL breaks at the first ';'. Encoding the ';' inside @import URLs as %3B keeps
the same fonts (Google reads it the same way) and lets the PDF render. Safe to run again.
"""
import re

import frappe

IMPORT_URL = re.compile(r"(@import\s+url\(\s*['\"]?)([^'\")]*)")


def encode(css):
    return IMPORT_URL.sub(lambda m: m.group(1) + m.group(2).replace(";", "%3B"), css or "")


def execute():
    for lh in frappe.get_all("Letter Head", fields=["name", "content", "footer"]):
        changes = {f: encode(lh[f]) for f in ("content", "footer") if lh[f] and encode(lh[f]) != lh[f]}
        if changes:
            frappe.db.set_value("Letter Head", lh.name, changes, update_modified=False)
            print("  Letter Head {0}: font @import fixed".format(lh.name))
