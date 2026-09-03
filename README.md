# MDC Solution – V1 (Real Single Rack Data)

This version uses the supplied:

`1 Rack SKU'S - MDC BOQ (01.09.2026)(1).xlsx`

## Real data loaded

- Single Rack Configuration 1
- Single Rack Configuration 2
- Single Rack Configuration 3
- Single Rack Configuration 4
- Configuration BOM/component details
- Unit cost values available in the source
- Optional accessory list and cost values
- Single-phase PDU list and cost values

## Future placeholder

Multirack Configuration 1–9 are currently:

`XXX - TO BE UPDATED`

The master data is separated into:

`data/MDC_Master_V1.xlsx`

so future data changes can be made in the Excel master rather than hard-coding them into the UI.

## Run

```bash
pip install -r requirements.txt
streamlit run app.py
```

Demo internal password:

`MDC@123`

For deployment, use Streamlit Secrets:

`MDC_INTERNAL_PASSWORD = "your-real-password"`

## Important pricing note

The source BOQ contains explicit unit costs for some lines and blank cost cells for others. Blank source costs are retained as unavailable rather than treated as real zero-cost components.

V1 calculates the configuration base cost from the explicit cost values supplied in the BOQ. Before production use, the company should confirm whether some blank-priced BOM lines are already included in the standard configuration cost.

For the final selling-price BOM, the margin price plus freight and installation are allocated proportionally across BOM lines with known cost so the BOM selling total reconciles to the calculated final selling price.

Warranty is calculated separately as:

`Margin Price × Warranty %`

and is not added again to the final selling price in V1, matching the interpretation of the handwritten requirement.
