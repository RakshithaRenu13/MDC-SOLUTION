# MDC Solution – Version 1

Streamlit prototype for the MDC rack/solution selection workflow.

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Demo internal password

`MDC@123`

Change this before deployment.

## Version 1 includes

- MDC Solution header with data-centre icon
- Sales / Internal-MDC mode
- Password-protected internal mode
- Customer details
- Single Rack / Multirack configuration selection
- 4 Single Rack configurations
- 9 Multirack configurations
- Optional accessories with quantity
- PDU selection with quantity
- Final structure
- Internal-only cost summary
- Margin / freight / installation / warranty calculations
- Final BOM with selling prices
- Internal cost Excel
- Sales Excel without cost information

## Important

This is a prototype using dummy data. The next version should move rack/configuration/component/accessory/PDU master data into Excel files and load them dynamically.
