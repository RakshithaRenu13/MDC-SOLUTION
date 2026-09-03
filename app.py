
import streamlit as st
import pandas as pd
from io import BytesIO

# ============================================================
# MDC SOLUTION - VERSION 1
# Prototype using dummy data.
# Replace the DATA section later with actual MDC master data.
# ============================================================

st.set_page_config(
    page_title="MDC Solution",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------------
# Demo authentication
# ---------------------------
INTERNAL_PASSWORD = "MDC@123"   # CHANGE THIS before deployment

# ---------------------------
# Dummy master data
# ---------------------------
CONFIGS = {
    "Single Rack": {
        "Configuration 1": {
            "base_cost": 75000,
            "components": [
                ("SR-C001", "Rack Frame Assembly", 1, "Nos", 32000, 25000),
                ("SR-C002", "Cable Management Kit", 1, "Set", 9000, 7000),
                ("SR-C003", "Monitoring Module", 1, "Nos", 18000, 14000),
                ("SR-C004", "Cooling Fan Assembly", 2, "Nos", 8000, 6000),
            ],
        },
        "Configuration 2": {
            "base_cost": 85000,
            "components": [
                ("SR-C011", "Rack Frame Assembly - Heavy Duty", 1, "Nos", 38000, 30000),
                ("SR-C012", "Cable Management Kit", 1, "Set", 9000, 7000),
                ("SR-C013", "Monitoring Module - Advanced", 1, "Nos", 22000, 17000),
                ("SR-C014", "Cooling Fan Assembly", 2, "Nos", 8000, 6000),
            ],
        },
        "Configuration 3": {
            "base_cost": 95000,
            "components": [
                ("SR-C021", "Rack Frame Assembly - Premium", 1, "Nos", 42000, 33000),
                ("SR-C022", "Cable Management Kit - Premium", 1, "Set", 11000, 8500),
                ("SR-C023", "Monitoring Module - Advanced", 1, "Nos", 24000, 19000),
                ("SR-C024", "Cooling Fan Assembly", 2, "Nos", 9000, 7000),
            ],
        },
        "Configuration 4": {
            "base_cost": 110000,
            "components": [
                ("SR-C031", "Rack Frame Assembly - Enterprise", 1, "Nos", 48000, 38000),
                ("SR-C032", "Cable Management Kit - Enterprise", 1, "Set", 13000, 10000),
                ("SR-C033", "Monitoring Module - Enterprise", 1, "Nos", 28000, 22000),
                ("SR-C034", "Cooling Fan Assembly", 2, "Nos", 10000, 8000),
            ],
        },
    },
    "Multirack": {
        f"Configuration {i}": {
            "base_cost": 120000 + (i - 1) * 15000,
            "components": [
                (f"MR-C{i}01", "Multi-Rack Frame Assembly", i, "Nos", 35000 + i*1000, 28000 + i*800),
                (f"MR-C{i}02", "Inter-Rack Coupling Kit", i, "Set", 12000 + i*500, 9500 + i*350),
                (f"MR-C{i}03", "Monitoring & Control Module", 1, "Nos", 25000 + i*700, 19500 + i*500),
                (f"MR-C{i}04", "Cooling Fan Assembly", i + 1, "Nos", 8000 + i*300, 6000 + i*250),
            ],
        }
        for i in range(1, 10)
    }
}

ACCESSORIES = [
    ("ACC001", "Temperature Sensor", "Digital temperature monitoring sensor", "Nos", 3500, 2500),
    ("ACC002", "Door Sensor", "Rack door open/close detection sensor", "Nos", 2800, 2000),
    ("ACC003", "Cable Tray", "Additional cable routing and support tray", "Nos", 4200, 3000),
    ("ACC004", "LED Rack Light", "Internal LED lighting assembly", "Nos", 1800, 1200),
    ("ACC005", "Blanking Panel", "Rack airflow management blanking panel", "Nos", 1200, 800),
]

PDUS = [
    ("PDU001", "Basic PDU", "Standard power distribution unit", "Nos", 6500, 4800),
    ("PDU002", "Metered PDU", "PDU with local power metering", "Nos", 10500, 8000),
    ("PDU003", "Monitored PDU", "Network monitored intelligent PDU", "Nos", 15500, 12000),
    ("PDU004", "Switched PDU", "Remote switched power distribution unit", "Nos", 18500, 14500),
]

# ---------------------------
# Session state
# ---------------------------
defaults = {
    "mode": "Sales",
    "authenticated": False,
    "customer_name": "",
    "customer_place": "",
    "problem": "",
    "solution": "",
    "mdc_type": "Single Rack",
    "configuration": "Configuration 1",
    "accessory_qty": {x[0]: 0 for x in ACCESSORIES},
    "pdu_qty": {x[0]: 0 for x in PDUS},
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ---------------------------
# Helpers
# ---------------------------
def money(x):
    return f"₹ {x:,.2f}"

def get_selected_config():
    return CONFIGS[st.session_state.mdc_type][st.session_state.configuration]

def build_bom():
    cfg = get_selected_config()
    rows = []

    for part, desc, qty, uom, sell, cost in cfg["components"]:
        rows.append({
            "S.No.": len(rows) + 1,
            "Part Code": part,
            "Description": desc,
            "Quantity": qty,
            "UOM": uom,
            "Unit Price": sell,
            "Total Price": sell * qty,
            "Unit Cost": cost,
            "Total Cost": cost * qty,
        })

    for part, desc, description, uom, sell, cost in ACCESSORIES:
        qty = st.session_state.accessory_qty.get(part, 0)
        if qty > 0:
            rows.append({
                "S.No.": len(rows) + 1,
                "Part Code": part,
                "Description": f"{desc} - {description}",
                "Quantity": qty,
                "UOM": uom,
                "Unit Price": sell,
                "Total Price": sell * qty,
                "Unit Cost": cost,
                "Total Cost": cost * qty,
            })

    for part, desc, description, uom, sell, cost in PDUS:
        qty = st.session_state.pdu_qty.get(part, 0)
        if qty > 0:
            rows.append({
                "S.No.": len(rows) + 1,
                "Part Code": part,
                "Description": f"{desc} - {description}",
                "Quantity": qty,
                "UOM": uom,
                "Unit Price": sell,
                "Total Price": sell * qty,
                "Unit Cost": cost,
                "Total Cost": cost * qty,
            })

    return pd.DataFrame(rows)

def build_internal_excel():
    bom = build_bom()
    output = BytesIO()

    customer = pd.DataFrame([
        ["Customer Name", st.session_state.customer_name],
        ["Customer Place", st.session_state.customer_place],
        ["Problem Description", st.session_state.problem],
        ["Solution", st.session_state.solution],
        ["MDC Type", st.session_state.mdc_type],
        ["Configuration", st.session_state.configuration],
    ], columns=["Field", "Value"])

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        customer.to_excel(writer, index=False, sheet_name="Customer & Configuration")
        bom.to_excel(writer, index=False, sheet_name="Final BOM")

        summary = pd.DataFrame([
            ["Base Cost", base_cost],
            ["Optional Cost", optional_cost],
            ["PDU Cost", pdu_cost],
            ["Total Cost", total_cost],
            ["Margin %", margin_pct],
            ["Margin Price", margin_price],
            ["Freight", freight],
            ["Installation", installation],
            ["Final Selling Price", final_selling_price],
            ["Warranty %", warranty_pct],
            ["Warranty Amount", warranty_amount],
        ], columns=["Item", "Value"])
        summary.to_excel(writer, index=False, sheet_name="Cost Summary")

    output.seek(0)
    return output

def build_sales_excel():
    bom = build_bom()[[
        "S.No.", "Part Code", "Description", "Quantity",
        "UOM", "Unit Price", "Total Price"
    ]]
    output = BytesIO()

    customer = pd.DataFrame([
        ["Customer Name", st.session_state.customer_name],
        ["Customer Place", st.session_state.customer_place],
        ["Problem Description", st.session_state.problem],
        ["Solution", st.session_state.solution],
        ["MDC Type", st.session_state.mdc_type],
        ["Configuration", st.session_state.configuration],
    ], columns=["Field", "Value"])

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        customer.to_excel(writer, index=False, sheet_name="Customer & Configuration")
        bom.to_excel(writer, index=False, sheet_name="Final BOM")

    output.seek(0)
    return output

# ---------------------------
# Header
# ---------------------------
st.markdown(
    """
    <div style="display:flex;align-items:center;gap:12px;margin-bottom:5px;">
        <div style="font-size:38px;">🏢</div>
        <div>
            <h1 style="margin:0;">MDC Solution</h1>
            <p style="margin:0;color:#666;">Rack Configuration & Solution Selection</p>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.divider()

# ---------------------------
# Sidebar mode
# ---------------------------
with st.sidebar:
    st.header("User Access")
    mode = st.radio(
        "Select User Type",
        ["Sales", "Internal – MDC"],
        index=0 if st.session_state.mode == "Sales" else 1
    )

    if mode != st.session_state.mode:
        st.session_state.mode = mode
        if mode == "Sales":
            st.session_state.authenticated = False
        st.rerun()

    if mode == "Internal – MDC":
        if not st.session_state.authenticated:
            st.warning("Internal access is protected.")
            password = st.text_input("MDC Password", type="password")
            if st.button("Unlock Internal Mode", use_container_width=True):
                if password == INTERNAL_PASSWORD:
                    st.session_state.authenticated = True
                    st.success("Access granted.")
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

# ---------------------------
# Customer Details
# ---------------------------
st.header("1. Customer Details")

c1, c2 = st.columns(2)
with c1:
    st.session_state.customer_name = st.text_input(
        "Customer Name", value=st.session_state.customer_name
    )
with c2:
    st.session_state.customer_place = st.text_input(
        "Customer Place", value=st.session_state.customer_place
    )

st.session_state.problem = st.text_area(
    "Problem Description", value=st.session_state.problem, height=90
)
st.session_state.solution = st.text_area(
    "Solution", value=st.session_state.solution, height=90
)

# ---------------------------
# Internal-only configuration
# ---------------------------
if is_internal:
    st.header("2. MDC Type & Configuration")

    c1, c2 = st.columns(2)
    with c1:
        mdc_type = st.radio(
            "MDC Type",
            ["Single Rack", "Multirack"],
            horizontal=True,
            index=0 if st.session_state.mdc_type == "Single Rack" else 1
        )
        if mdc_type != st.session_state.mdc_type:
            st.session_state.mdc_type = mdc_type
            st.session_state.configuration = "Configuration 1"
            st.rerun()

    with c2:
        configs = list(CONFIGS[st.session_state.mdc_type].keys())
        st.session_state.configuration = st.selectbox(
            "Select Configuration",
            configs,
            index=configs.index(st.session_state.configuration)
        )

    st.markdown(
        f"### **Selected Configuration: {st.session_state.mdc_type} – {st.session_state.configuration}**"
    )
else:
    # Sales can see the selected configuration, but cannot change it.
    st.header("2. Selected Configuration")
    st.info(
        "Configuration is selected by MDC Internal users. "
        "Sales users can view the selected configuration."
    )

# ---------------------------
# Optional accessories
# ---------------------------
st.header("3. Optional Accessories")

st.caption("Select required accessories and update quantity. Prices are not displayed in this section.")

for part, desc, description, uom, sell, cost in ACCESSORIES:
    col1, col2, col3 = st.columns([2, 5, 2])
    with col1:
        selected = st.checkbox(
            desc,
            value=st.session_state.accessory_qty.get(part, 0) > 0,
            key=f"acc_check_{part}"
        )
    with col2:
        st.write(description)
        st.caption(f"Part Code: {part} | UOM: {uom}")
    with col3:
        if selected:
            st.session_state.accessory_qty[part] = st.number_input(
                "Qty",
                min_value=1,
                max_value=999,
                value=max(1, st.session_state.accessory_qty.get(part, 0)),
                step=1,
                key=f"acc_qty_{part}",
            )
        else:
            st.session_state.accessory_qty[part] = 0

# ---------------------------
# PDU
# ---------------------------
st.header("4. PDU Selection")

st.caption("Select required PDU components and update quantity. Prices are not displayed in this section.")

for part, desc, description, uom, sell, cost in PDUS:
    col1, col2, col3 = st.columns([2, 5, 2])
    with col1:
        selected = st.checkbox(
            desc,
            value=st.session_state.pdu_qty.get(part, 0) > 0,
            key=f"pdu_check_{part}"
        )
    with col2:
        st.write(description)
        st.caption(f"Part Code: {part} | UOM: {uom}")
    with col3:
        if selected:
            st.session_state.pdu_qty[part] = st.number_input(
                "Qty",
                min_value=1,
                max_value=999,
                value=max(1, st.session_state.pdu_qty.get(part, 0)),
                step=1,
                key=f"pdu_qty_{part}",
            )
        else:
            st.session_state.pdu_qty[part] = 0

# ---------------------------
# Final Structure - common
# ---------------------------
st.header("5. Final Structure")

bom = build_bom()

if not bom.empty:
    structure = bom[[
        "S.No.", "Part Code", "Description", "Quantity", "UOM"
    ]]
    st.dataframe(structure, use_container_width=True, hide_index=True)
else:
    st.info("No components selected yet.")

# ---------------------------
# Internal Cost + Price
# ---------------------------
base_cost = get_selected_config()["base_cost"]
bom = build_bom()

optional_cost = sum(
    r["Total Cost"]
    for _, r in bom.iterrows()
    if str(r["Part Code"]).startswith("ACC")
)
pdu_cost = sum(
    r["Total Cost"]
    for _, r in bom.iterrows()
    if str(r["Part Code"]).startswith("PDU")
)
total_cost = base_cost + optional_cost + pdu_cost

margin_pct = 20.0
freight = 0.0
installation = 0.0
warranty_pct = 0.0
margin_price = total_cost / (1 - margin_pct / 100)
final_selling_price = margin_price
warranty_amount = 0.0

if is_internal:
    st.header("6. Cost Summary – Internal Only")

    a, b, c, d = st.columns(4)
    a.metric("Base Cost", money(base_cost))
    b.metric("Optional Cost", money(optional_cost))
    c.metric("PDU Cost", money(pdu_cost))
    d.metric("Total Cost", money(total_cost))

    st.header("7. Cost to Selling Price – Internal Only")

    p1, p2, p3, p4 = st.columns(4)
    with p1:
        margin_pct = st.number_input(
            "Margin (%)", min_value=0.0, max_value=99.0,
            value=20.0, step=0.5
        )
    with p2:
        freight = st.number_input(
            "Freight", min_value=0.0, value=0.0, step=500.0
        )
    with p3:
        installation = st.number_input(
            "Installation", min_value=0.0, value=0.0, step=500.0
        )
    with p4:
        warranty_pct = st.number_input(
            "Warranty (%)", min_value=0.0, max_value=100.0,
            value=0.0, step=0.5
        )

    margin_price = total_cost / (1 - margin_pct / 100)
    final_selling_price = margin_price + freight + installation
    warranty_amount = margin_price * (warranty_pct / 100)

    q1, q2, q3, q4 = st.columns(4)
    q1.metric("Margin Price", money(margin_price))
    q2.metric("After Freight", money(margin_price + freight))
    q3.metric("Final Selling Price", money(final_selling_price))
    q4.metric("Warranty Amount", money(warranty_amount))

# ---------------------------
# Final BOM
# ---------------------------
st.header("8. Final BOM")

final_bom = build_bom()

if not final_bom.empty:
    display_bom = final_bom[[
        "S.No.", "Part Code", "Description", "Quantity",
        "UOM", "Unit Price", "Total Price"
    ]].copy()

    display_bom["Unit Price"] = display_bom["Unit Price"].map(money)
    display_bom["Total Price"] = display_bom["Total Price"].map(money)

    st.dataframe(display_bom, use_container_width=True, hide_index=True)

    st.metric(
        "BOM Selling Value",
        money(final_bom["Total Price"].sum())
    )
else:
    st.info("No BOM available.")

# ---------------------------
# Excel downloads
# ---------------------------
st.header("9. Excel Download")

if is_internal:
    st.success("Internal MDC user: both Internal Cost Excel and Sales Excel are available.")

    c1, c2 = st.columns(2)
    with c1:
        st.download_button(
            "⬇️ Download Internal Cost Excel",
            data=build_internal_excel(),
            file_name="MDC_Internal_Cost.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
    with c2:
        st.download_button(
            "⬇️ Download Sales Excel",
            data=build_sales_excel(),
            file_name="MDC_Sales_Output.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
else:
    st.download_button(
        "⬇️ Download Sales Excel",
        data=build_sales_excel(),
        file_name="MDC_Sales_Output.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )

st.divider()
st.caption("MDC Solution – Version 1 Prototype | Replace demo master data and password before production use.")
