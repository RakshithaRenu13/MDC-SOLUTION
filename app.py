
import os
from io import BytesIO

import pandas as pd
import streamlit as st

# ============================================================
# MDC SOLUTION - VERSION 1 (REAL SINGLE-RACK DATA)
# Data source: MDC_Master_V1.xlsx (same folder as app.py)
#
# Single Rack:
#   Configuration 1-4 = real data from supplied MDC BOQ
#
# Multirack:
#   Configuration 1-9 = XXX placeholders for future update
# ============================================================

st.set_page_config(
    page_title="MDC Solution",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded",
)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MASTER_FILE = os.path.join(BASE_DIR, "MDC_Master_V1.xlsx")
DEMO_INTERNAL_PASSWORD = "MDC@123"  # Change before production.

# ------------------------------------------------------------
# Load master data
# ------------------------------------------------------------
@st.cache_data
def load_master():
    configs = pd.read_excel(MASTER_FILE, sheet_name="Configurations")
    components = pd.read_excel(MASTER_FILE, sheet_name="Components")
    accessories = pd.read_excel(MASTER_FILE, sheet_name="Accessories")
    pdus = pd.read_excel(MASTER_FILE, sheet_name="PDUs")
    return configs, components, accessories, pdus

configs_df, components_df, accessories_df, pdus_df = load_master()

# ------------------------------------------------------------
# Session state
# ------------------------------------------------------------
defaults = {
    "mode": "Sales",
    "authenticated": False,
    "customer_name": "",
    "customer_place": "",
    "problem": "",
    "solution": "",
    "mdc_type": "Single Rack",
    "configuration": "Configuration 1",
    "accessory_qty": {},
    "pdu_qty": {},
    "margin_pct": 20.0,
    "freight": 0.0,
    "installation": 0.0,
    "warranty_pct": 0.0,
}
for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

def money(value):
    return f"₹ {value:,.2f}"


def price_box(label, value):
    st.markdown(
        f"""
        <div style="padding:4px 0 12px 0; min-height:82px; overflow:visible;">
            <div style="font-size:16px; color:#4b5563; margin-bottom:7px;">
                {label}
            </div>
            <div style="font-size:30px; font-weight:600; color:#30333d;
                        white-space:nowrap; overflow:visible;">
                {money(value)}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def internal_password():
    # Streamlit Cloud / deployment can use st.secrets["MDC_INTERNAL_PASSWORD"].
    try:
        return st.secrets["MDC_INTERNAL_PASSWORD"]
    except Exception:
        return DEMO_INTERNAL_PASSWORD

def selected_config_record():
    match = configs_df[
        (configs_df["MDC Type"] == st.session_state.mdc_type)
        & (configs_df["Configuration"] == st.session_state.configuration)
    ]
    return match.iloc[0] if not match.empty else None

def selected_components():
    return components_df[
        (components_df["MDC Type"] == st.session_state.mdc_type)
        & (components_df["Configuration"] == st.session_state.configuration)
    ].copy()

def build_bom():
    rows = []

    # Configuration BOM
    for _, r in selected_components().iterrows():
        cost = r["Unit Cost"]
        qty = float(r["Quantity"])
        rows.append({
            "S.No.": len(rows) + 1,
            "Component Type": "Base (Configuration)",
            "Part Code": r["Part Code"] if pd.notna(r["Part Code"]) and str(r["Part Code"]).strip() and str(r["Part Code"]).lower() != "nan" else "",
            "Description": r["Description"],
            "Quantity": qty,
            "UOM": r["UOM"],
            "Unit Cost": cost,
            "Total Cost": cost * qty if pd.notna(cost) else None,
            "Source": "Configuration",
        })

    # Optional accessories
    for _, r in accessories_df.iterrows():
        part = str(r["Part Code"])
        qty = float(st.session_state.accessory_qty.get(part, 0))
        if qty > 0:
            cost = r["Unit Cost"]
            rows.append({
                "S.No.": len(rows) + 1,
                "Component Type": "Optional Accessory",
                "Part Code": part if part.strip() and part.lower() != "nan" else "",
                "Description": r["Description"],
                "Quantity": qty,
                "UOM": r["UOM"],
                "Unit Cost": cost,
                "Total Cost": cost * qty if pd.notna(cost) else None,
                "Source": "Optional Accessory",
            })

    # 
    for _, r in pdus_df.iterrows():
        part = str(r["Part Code"])
        qty = float(st.session_state.pdu_qty.get(part, 0))
        if qty > 0:
            cost = r["Unit Cost"]
            desc = f'{r["Description"]} | Type: {r["Type"]} | C13: {r["C13"]} | C19: {r["C19"]}'
            rows.append({
                "S.No.": len(rows) + 1,
                "Component Type": "PDU",
                "Part Code": part if part.strip() and part.lower() != "nan" else "",
                "Description": desc,
                "Quantity": qty,
                "UOM": r["UOM"],
                "Unit Cost": cost,
                "Total Cost": cost * qty if pd.notna(cost) else None,
                "Source": "PDU",
            })

    return pd.DataFrame(rows)

def cost_summary(bom):
    cfg = selected_config_record()
    base_cost = float(cfg["Base Cost"]) if cfg is not None and pd.notna(cfg["Base Cost"]) else 0.0

    optional_cost = 0.0
    pdu_cost = 0.0

    if not bom.empty:
        optional_cost = float(
            bom.loc[bom["Source"] == "Optional Accessory", "Total Cost"]
            .fillna(0).sum()
        )
        pdu_cost = float(
            bom.loc[bom["Source"] == "PDU", "Total Cost"]
            .fillna(0).sum()
        )

    total_cost = base_cost + optional_cost + pdu_cost
    return base_cost, optional_cost, pdu_cost, total_cost

def add_selling_prices(bom, total_cost, margin_pct, freight, installation):
    result = bom.copy()

    # Cost-based margin conversion.
    margin_price = total_cost / (1 - margin_pct / 100) if margin_pct < 100 else 0
    final_selling_price = margin_price + freight + installation

    # Allocate the final selling price proportionally to known-cost BOM lines.
    # This makes BOM Total Price reconcile to the final selling price.
    known_cost_total = result["Total Cost"].fillna(0).sum() if not result.empty else 0

    if known_cost_total > 0:
        result["Total Price"] = result["Total Cost"].fillna(0) / known_cost_total * final_selling_price
        result["Unit Price"] = result["Total Price"] / result["Quantity"]
    else:
        result["Total Price"] = pd.NA
        result["Unit Price"] = pd.NA

    return result, margin_price, final_selling_price

def customer_table():
    return pd.DataFrame([
        ["Customer Name", st.session_state.customer_name],
        ["Customer Place", st.session_state.customer_place],
        ["Problem Description", st.session_state.problem],
        ["Solution", st.session_state.solution],
        ["MDC Type", st.session_state.mdc_type],
        ["Configuration", st.session_state.configuration],
    ], columns=["Field", "Value"])

def excel_bytes(internal=False, bom=None, cost_data=None, final_selling_price=0.0):
    output = BytesIO()

    cust = customer_table()

    if bom is None:
        bom = build_bom()

    # --------------------------------------------------------
    # Create ONE combined Excel sheet only
    # --------------------------------------------------------
    with pd.ExcelWriter(output, engine="openpyxl") as writer:

        sheet_name = "MDC Solution"

        # ====================================================
        # CUSTOMER DETAILS & CONFIGURATION
        # ====================================================
        start_row = 0

        cust.to_excel(
            writer,
            index=False,
            sheet_name=sheet_name,
            startrow=start_row
        )

        start_row += len(cust) + 3

        # ====================================================
        # INTERNAL EXCEL
        # ====================================================
        if internal:

            # -------------------------------
            # Internal Cost BOM
            # -------------------------------
            pd.DataFrame(
                [["INTERNAL COST BOM"]],
                columns=["Section"]
            ).to_excel(
                writer,
                index=False,
                sheet_name=sheet_name,
                startrow=start_row
            )

            start_row += 2

            internal_cols = [
                "S.No.",
                "Component Type",
                "Part Code",
                "Description",
                "Quantity",
                "UOM",
                "Unit Cost",
                "Total Cost",
                "Unit Price",
                "Total Price"
            ]

            internal_bom = bom[internal_cols].copy()

            internal_bom.to_excel(
                writer,
                index=False,
                sheet_name=sheet_name,
                startrow=start_row
            )

            start_row += len(internal_bom) + 3

            # -------------------------------
            # Cost Summary
            # -------------------------------
            pd.DataFrame(
                [["COST SUMMARY"]],
                columns=["Section"]
            ).to_excel(
                writer,
                index=False,
                sheet_name=sheet_name,
                startrow=start_row
            )

            start_row += 2

            summary_data = []

            if cost_data is not None:
                summary_data.extend(cost_data)

            # Ensure Final Selling Price is included
            if not any(
                str(row[0]).strip().lower() == "final selling price"
                for row in summary_data
            ):
                summary_data.append(
                    ["Final Selling Price", final_selling_price]
                )

            summary_df = pd.DataFrame(
                summary_data,
                columns=["Item", "Value"]
            )

            summary_df.to_excel(
                writer,
                index=False,
                sheet_name=sheet_name,
                startrow=start_row
            )

        # ====================================================
        # SALES EXCEL
        # ====================================================
        else:

            # -------------------------------
            # Final BOM
            # -------------------------------
            pd.DataFrame(
                [["FINAL BOM"]],
                columns=["Section"]
            ).to_excel(
                writer,
                index=False,
                sheet_name=sheet_name,
                startrow=start_row
            )

            start_row += 2

            sales_cols = [
                "S.No.",
                "Component Type",
                "Part Code",
                "Description",
                "Quantity",
                "UOM",
                "Unit Price",
                "Total Price"
            ]

            sales_bom = bom[sales_cols].copy()

            sales_bom.to_excel(
                writer,
                index=False,
                sheet_name=sheet_name,
                startrow=start_row
            )

            start_row += len(sales_bom) + 3

            # -------------------------------
            # Final Selling Price
            # -------------------------------
            pd.DataFrame(
                [
                    ["FINAL SELLING PRICE", final_selling_price]
                ],
                columns=["Item", "Value"]
            ).to_excel(
                writer,
                index=False,
                sheet_name=sheet_name,
                startrow=start_row
            )

    output.seek(0)
    return output

# ------------------------------------------------------------
# Header
# ------------------------------------------------------------
st.markdown(
    """
    <div style="display:flex;align-items:center;gap:12px;">
        <div style="font-size:42px;">🏢</div>
        <div>
            <h1 style="margin:0;">MDC Solution</h1>
            <div style="color:#666;">Rack Configuration & Solution Selection</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)
st.divider()

# ------------------------------------------------------------
# Access mode
# ------------------------------------------------------------
with st.sidebar:
    st.header("User Access")

    mode = st.radio(
        "Select User Type",
        ["Sales", "Internal – MDC"],
        index=0 if st.session_state.mode == "Sales" else 1,
    )

    if mode != st.session_state.mode:
        st.session_state.mode = mode
        if mode == "Sales":
            st.session_state.authenticated = False
        st.rerun()

    if mode == "Internal – MDC":
        if not st.session_state.authenticated:
            st.warning("Internal MDC access requires a password.")
            pwd = st.text_input("MDC Password", type="password")
            if st.button("Unlock Internal Mode", use_container_width=True):
                if pwd == internal_password():
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error("Incorrect password.")
        else:
            st.success("Internal mode unlocked.")
            if st.button("Lock Internal Mode", use_container_width=True):
                st.session_state.authenticated = False
                st.session_state.mode = "Sales"
                st.rerun()

is_internal = (
    st.session_state.mode == "Internal – MDC"
    and st.session_state.authenticated
)

# ------------------------------------------------------------
# 1 Customer details
# ------------------------------------------------------------
st.header("1. Customer Details")

c1, c2 = st.columns(2)
with c1:
    st.session_state.customer_name = st.text_input(
        "Customer Name", st.session_state.customer_name
    )
with c2:
    st.session_state.customer_place = st.text_input(
        "Customer Place", st.session_state.customer_place
    )

st.session_state.problem = st.text_area(
    "Problem Description", st.session_state.problem, height=90
)
st.session_state.solution = st.text_area(
    "Solution", st.session_state.solution, height=90
)

# ------------------------------------------------------------
# 2 MDC Type & Configuration
# Both Sales and Internal users can select MDC type/configuration.
# ------------------------------------------------------------
st.header("2. MDC Type & Configuration")

mdc_type = st.radio(
    "MDC Type",
    ["Single Rack", "Multirack"],
    horizontal=True,
    index=0 if st.session_state.mdc_type == "Single Rack" else 1,
)

if mdc_type != st.session_state.mdc_type:
    st.session_state.mdc_type = mdc_type
    st.session_state.configuration = "Configuration 1"
    st.session_state.accessory_qty = {}
    st.session_state.pdu_qty = {}
    st.rerun()

available = configs_df[
    configs_df["MDC Type"] == st.session_state.mdc_type
].copy()

labels = available["Configuration"].tolist()

if labels:
    st.session_state.configuration = st.selectbox(
        "Select Configuration",
        labels,
        index=labels.index(st.session_state.configuration)
        if st.session_state.configuration in labels else 0,
    )

cfg = selected_config_record()
if cfg is not None:
    if cfg["Status"] == "REAL DATA":
        st.success(
            f'**Selected Configuration: {cfg["Configuration"]} — {cfg["Configuration Title"]}**'
        )
    else:
        st.warning(
            f'**Selected Configuration: {cfg["Configuration"]} — {cfg["Configuration Title"]}**'
        )

# if not is_internal:
#     st.caption(
#         "Sales can select Single Rack/Multirack and the required configuration. "
#         "Internal cost information remains hidden."
#     )

# ------------------------------------------------------------
# 3 Optional accessories
# ------------------------------------------------------------
st.header("3. Optional Accessories")
# st.caption("Select accessories and update quantity. Prices are intentionally not shown here.")

for _, r in accessories_df.iterrows():
    part = str(r["Part Code"])
    key_check = f"acc_check_{part}"
    key_qty = f"acc_qty_{part}"

    selected = st.checkbox(
        f'{part} — {r["Description"]}',
        value=st.session_state.accessory_qty.get(part, 0) > 0,
        key=key_check,
    )

    cols = st.columns([6, 2, 2])
    # with cols[0]:
    #     st.caption(f'UOM: {r["UOM"]} | Pricing status: {r["Pricing Status"]}')
    with cols[1]:
        if selected:
            qty = st.number_input(
                "Quantity",
                min_value=1,
                max_value=999,
                value=max(1, int(st.session_state.accessory_qty.get(part, 1))),
                step=1,
                key=key_qty,
            )
            st.session_state.accessory_qty[part] = qty
        else:
            st.session_state.accessory_qty[part] = 0

# ------------------------------------------------------------
# 4 PDU selection
# ------------------------------------------------------------
st.header("4. PDU Selection")

pdu_options = [
    f'{r["Part Code"]} — {r["Description"]}'
    for _, r in pdus_df.iterrows()
]

selected_pdu = st.selectbox(
    "Select PDU",
    ["None"] + pdu_options,
    index=0
)

# Reset PDU selection
st.session_state.pdu_qty = {}

if selected_pdu != "None":

    selected_index = pdu_options.index(selected_pdu)
    selected_row = pdus_df.iloc[selected_index]

    part = str(selected_row["Part Code"])

    qty = st.number_input(
        "PDU Quantity",
        min_value=1,
        max_value=999,
        value=1,
        step=1
    )

    st.session_state.pdu_qty[part] = qty

    st.caption(
        f'Type: {selected_row["Type"]} | '
        f'C13: {selected_row["C13"]} | '
        f'C19: {selected_row["C19"]} | '
        f'UOM: {selected_row["UOM"]}'
    )
# st.header("4. PDU Selection")
# # st.caption("Select PDU components and update quantity. Prices are intentionally not shown here.")

# for _, r in pdus_df.iterrows():
#     part = str(r["Part Code"])
#     key_check = f"pdu_check_{part}"
#     key_qty = f"pdu_qty_{part}"

#     selected = st.selectbox(
#         f'{part} — {r["Description"]}',
#         value=st.session_state.pdu_qty.get(part, 0) > 0,
#         key=key_check,
#     )

#     cols = st.columns([6, 2, 2])
#     # with cols[0]:
#     #     st.caption(
#     #         f'Type: {r["Type"]} | C13: {r["C13"]} | C19: {r["C19"]} | UOM: {r["UOM"]}'
#     #     )
#     with cols[1]:
#         if selected:
#             qty = st.number_input(
#                 "Quantity",
#                 min_value=1,
#                 max_value=999,
#                 value=max(1, int(st.session_state.pdu_qty.get(part, 1))),
#                 step=1,
#                 key=key_qty,
#             )
#             st.session_state.pdu_qty[part] = qty
#         else:
#             st.session_state.pdu_qty[part] = 0

# ------------------------------------------------------------
# 5 Final structure - common to both users
# ------------------------------------------------------------
st.header("5. Final Structure")

bom = build_bom()

if not bom.empty:
    structure = bom[[
        "S.No.", "Component Type", "Part Code", "Description", "Quantity", "UOM"
    ]].copy()
    st.dataframe(structure, use_container_width=True, hide_index=True)
else:
    st.info("No components selected.")

# ------------------------------------------------------------
# Cost + selling price - internal only
# ------------------------------------------------------------
base_cost, optional_cost, pdu_cost, total_cost = cost_summary(bom)

margin_pct = st.session_state.margin_pct
freight = st.session_state.freight
installation = st.session_state.installation
warranty_pct = st.session_state.warranty_pct

if is_internal:
    st.header("6. Cost Summary — Internal Only")

    a, b, c, d = st.columns(4)
    with a:
        price_box("Base Cost", base_cost)
    with b:
        price_box("Optional Cost", optional_cost)
    with c:
        price_box("PDU Cost", pdu_cost)
    with d:
        price_box("Total Cost", total_cost)

    st.header("7. Cost to Selling Price")

    p1, p2, p3, p4 = st.columns(4)
    with p1:
        margin_pct = st.number_input(
            "Margin (%)", 0.0, 99.0,
            st.session_state.margin_pct, 0.5
        )
        st.session_state.margin_pct = margin_pct
    with p2:
        freight = st.number_input(
            "Freight", 0.0,
            value=st.session_state.freight, step=500.0
        )
        st.session_state.freight = freight
    with p3:
        installation = st.number_input(
            "Installation", 0.0,
            value=st.session_state.installation, step=500.0
        )
        st.session_state.installation = installation
    with p4:
        warranty_pct = st.number_input(
            "Warranty (%)", 0.0, 100.0,
            st.session_state.warranty_pct, 0.5
        )
        st.session_state.warranty_pct = warranty_pct

    margin_price = total_cost / (1 - margin_pct / 100) if margin_pct < 100 else 0
    final_selling_price = margin_price + freight + installation
    warranty_amount =( (margin_price * warranty_pct / 100)+margin_price)

    a, b, c, d = st.columns(4)
    with a:
        price_box("Margin Price", margin_price)
    with b:
        price_box("After Freight", margin_price + freight)
    with c:
        price_box("Final Selling Price", final_selling_price)
    with d:
        price_box("Warranty Amount", warranty_amount)

# ------------------------------------------------------------
# 8 Final BOM
# ------------------------------------------------------------
st.header("8. Final BOM")

if not bom.empty:
    bom_with_price, margin_price, final_selling_price = add_selling_prices(
        bom, total_cost, margin_pct, freight, installation
    )

    display = bom_with_price[[
        "S.No.", "Component Type", "Part Code", "Description", "Quantity",
        "UOM", "Unit Price", "Total Price"
    ]].copy()

    display["Unit Price"] = display["Unit Price"].apply(
        lambda x: money(float(x)) if pd.notna(x) else "N/A"
    )
    display["Total Price"] = display["Total Price"].apply(
        lambda x: money(float(x)) if pd.notna(x) else "N/A"
    )

    st.dataframe(display, use_container_width=True, hide_index=True)

    known = bom_with_price["Total Price"].dropna().sum()
    price_box("BOM Selling Value", float(known))

    # if not is_internal:
    #     st.caption("Sales view contains selling prices only. Internal unit cost and total cost are not displayed.")
else:
    bom_with_price = bom
    st.info("No BOM available.")

# ------------------------------------------------------------
# 9 Excel
# ------------------------------------------------------------
st.header("9. Excel Download")

if not bom.empty:
    internal_cost_data = [
        ["Base Cost", base_cost],
        ["Optional Cost", optional_cost],
        ["PDU Cost", pdu_cost],
        ["Total Cost", total_cost],
        ["Margin %", margin_pct],
        ["Margin Price", margin_price if is_internal else 0],
        ["Freight", freight if is_internal else 0],
        ["Installation", installation if is_internal else 0],
        ["Final Selling Price", final_selling_price if is_internal else 0],
        ["Warranty %", warranty_pct if is_internal else 0],
        ["Warranty Amount", (margin_price * warranty_pct / 100) if is_internal else 0],
    ]

    # Sales Excel is always safe for both roles.
    sales_file = excel_bytes(
        internal=False,
        bom=bom_with_price,
        cost_data=None,
        final_selling_price=final_selling_price,
    )

    if is_internal:
        st.success("Internal MDC user: both Excel versions are available.")

        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                "⬇️ Download Internal Cost Excel",
                data=excel_bytes(
                    internal=True,
                    bom=bom_with_price,
                    cost_data=internal_cost_data,
                    final_selling_price=final_selling_price,
                ),
                file_name="MDC_Internal_Cost.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
        with col2:
            st.download_button(
                "⬇️ Download Sales Excel",
                data=sales_file,
                file_name="MDC_Sales_Output.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
    else:
        st.download_button(
            "⬇️ Download Sales Excel",
            data=sales_file,
            file_name="MDC_Sales_Output.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )

st.divider()
st.caption(
    "MDC Solution V1 | Single Rack data loaded from the supplied 01.09.2026 BOQ | "
    "Multirack configurations are XXX placeholders for future updates."
)
