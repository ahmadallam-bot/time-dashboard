"""
Categorization config.  Edit this file to refine how events are bucketed.

- COLORS: fixed colour per category (keeps charts consistent across weeks).
- RULES:  (keyword, category) pairs. The event title is lower-cased and the
          FIRST keyword found (top to bottom) wins. Order matters.
- FALLBACK: where anything unmatched lands. Keep as "Uncategorized" so you can
          see what still needs a rule, then add keywords over time.
"""

COLORS = {
    "Admin, Email & Misc":      "#64748b",
    "Inventory / Forecasting":  "#2563eb",
    "Break / Lunch":            "#c3d0d9",
    "Refurbishment":            "#f59e0b",
    "Ciao / Delivery Ops":      "#0891b2",
    "Tech / Systems":           "#7c3aed",
    "Recurring Syncs":          "#db2777",
    "Hiring & SOP":             "#16a34a",
    "1:1s & Catchups":          "#ea580c",
    "Shipa Transition":         "#0d9488",
    "Order Management":         "#eab308",
    "Supplier Syncs":           "#9333ea",
    "Showroom":                 "#be123c",
    "Learning":                 "#0ea5e9",
    "Uncategorized":            "#cbd5e1",
}

# Order matters - first match wins. More specific rules go higher.
RULES = [
    ("shipa",            "Shipa Transition"),
    ("ship a",           "Shipa Transition"),
    ("refurb",           "Refurbishment"),
    ("refub",            "Refurbishment"),          # common typo
    ("order management", "Order Management"),        # before "filter"/"order"
    ("inventory",        "Inventory / Forecasting"),
    ("innventory",       "Inventory / Forecasting"), # common typo
    ("forecast",         "Inventory / Forecasting"),
    ("shipment",         "Inventory / Forecasting"),
    ("mac id",           "Tech / Systems"),
    ("ciao",             "Ciao / Delivery Ops"),
    ("canister",         "Ciao / Delivery Ops"),
    ("return",           "Ciao / Delivery Ops"),
    ("scheduling",       "Ciao / Delivery Ops"),
    ("waqas",            "Ciao / Delivery Ops"),
    ("tracker",          "Ciao / Delivery Ops"),
    ("filter",           "Ciao / Delivery Ops"),
    ("jose",             "Tech / Systems"),
    ("zoho",             "Tech / Systems"),
    ("s&op",             "Recurring Syncs"),
    ("ops cx",           "Recurring Syncs"),
    ("freight",          "Recurring Syncs"),
    ("weekly sync",      "Recurring Syncs"),
    ("olansi",           "Supplier Syncs"),
    ("production sync",  "Supplier Syncs"),
    ("sop",              "Hiring & SOP"),
    ("interview",        "Hiring & SOP"),
    ("hafeez",           "Hiring & SOP"),
    ("hiring",           "Hiring & SOP"),
    ("technician",       "Hiring & SOP"),
    ("kpi",              "Admin, Email & Misc"),
    ("showroom",         "Showroom"),
    ("north star",       "Learning"),
    ("learning",         "Learning"),
    ("planning",         "Admin, Email & Misc"),
    ("mail",             "Admin, Email & Misc"),
    ("break",            "Break / Lunch"),
    ("lunch",            "Break / Lunch"),
    ("catch",            "1:1s & Catchups"),
    ("/ ahmad",          "1:1s & Catchups"),
    ("/ahmad",           "1:1s & Catchups"),
    ("sherif",           "1:1s & Catchups"),
    ("alexi",            "1:1s & Catchups"),
    ("layal",            "1:1s & Catchups"),
    ("abdul",            "1:1s & Catchups"),
    ("mohamad",          "1:1s & Catchups"),
    ("others",           "Admin, Email & Misc"),
    ("other",            "Admin, Email & Misc"),
    ("planning",         "Admin, Email & Misc"),
]

FALLBACK = "Uncategorized"


def classify(title: str) -> str:
    t = (title or "").lower()
    for kw, cat in RULES:
        if kw in t:
            return cat
    return FALLBACK


def color_for(category: str) -> str:
    return COLORS.get(category, "#94a3b8")
