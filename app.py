import pandas as pd
import gradio as gr
import re  # ✅ Add this line to fix the error
import OS

# ✅ Use GitHub Raw URLs for Faster CSV Loading
CSV_PATHS = {
    "Fortinet": "https://raw.githubusercontent.com/rajeesh668/firewall-comparison-tool/main/Fortinet%20FW%20Models.csv",
    "Palo Alto": "https://raw.githubusercontent.com/rajeesh668/firewall-comparison-tool/main/PaloAlto%20Spec.csv",
    "SonicWall": "https://raw.githubusercontent.com/rajeesh668/firewall-comparison-tool/main/SonicWall%20Spec.csv",
    "Sophos": "https://raw.githubusercontent.com/rajeesh668/firewall-comparison-tool/main/Sophos_XGS_All_Models_Performance.csv"
}

# ✅ Function to Load CSVs from GitHub
def load_csv_data(url, vendor_name):
    """Load CSV safely. Return an empty DataFrame if the file is missing."""
    try:
        df = pd.read_csv(url)
        print(f"✅ Successfully loaded {vendor_name} data - First 5 rows:")
        print(df.head())
        return df
    except Exception as e:
        print(f"❌ Could not load {vendor_name} data: {e}")
        return pd.DataFrame()

fortinet_data = load_csv_data(CSV_PATHS["Fortinet"], "Fortinet")
paloalto_data = load_csv_data(CSV_PATHS["Palo Alto"], "Palo Alto")
sonicwall_data = load_csv_data(CSV_PATHS["SonicWall"], "SonicWall")
sophos_data = load_csv_data(CSV_PATHS["Sophos"], "Sophos")

# 🔹 Vendor Specific Columns
FORTINET_COLS = ["Firewall Throughput (Gbps)", "IPS Throughput (Gbps)", "Threat Protection Throughput (Gbps)", "NGFW Throughput (Gbps)", "IPsec VPN Throughput (Gbps)"]
PALOALTO_COLS = ["Firewall Throughput (Gbps)", "Threat Protection Throughput (Gbps)", "IPsec VPN Throughput (Gbps)"]
SONICWALL_COLS = ["Firewall Throughput (Gbps)", "IPS Throughput (Gbps)", "Threat Protection Throughput (Gbps)", "IPsec VPN Throughput (Gbps)"]

ALL_COLUMNS = list(set(FORTINET_COLS + PALOALTO_COLS + SONICWALL_COLS))

# 🔹 Extract Highest Value from Slash-Separated Strings
def extract_max_throughput(value):
    if isinstance(value, str):
        nums = [float(num) for num in re.findall(r"\d+\.?\d*", value)]
        return max(nums) if nums else None
    return value

# 🔹 Parse + Convert Data
def parse_and_convert(df, col_list):
    for c in col_list:
        if c in df.columns:
            df[c] = df[c].apply(extract_max_throughput)
            df[c] = pd.to_numeric(df[c], errors='coerce')

parse_and_convert(fortinet_data, FORTINET_COLS)
parse_and_convert(paloalto_data, PALOALTO_COLS)
parse_and_convert(sonicwall_data, SONICWALL_COLS)
parse_and_convert(sophos_data, ALL_COLUMNS)

# 🔹 Get Models for Selected Vendor
def get_models(vendor):
    if vendor == "Fortinet":
        return fortinet_data["Model"].dropna().unique().tolist()
    elif vendor == "Palo Alto":
        return paloalto_data["Model"].dropna().unique().tolist()
    elif vendor == "SonicWall":
        return sonicwall_data["Model"].dropna().unique().tolist()
    return []

# 🔹 Build Matching Score Table
def build_matching_table(vendor_row, sophos_row, relevant_cols):
    dev_dict = {
        "Metric": relevant_cols,
        f"{vendor_row['Model']} Value": [vendor_row[col] for col in relevant_cols],
        f"{sophos_row['Model']} Value": [sophos_row[col] for col in relevant_cols],
        "Matching %": [f"{(sophos_row[col] / vendor_row[col]) * 100:.1f}%" if vendor_row[col] != 0 else "N/A" for col in relevant_cols]
    }
    return pd.DataFrame(dev_dict)

# 🔹 Compare Models
def compare_models(vendor, model, manual=False, chosen_sophos=None):
    if vendor == "Fortinet":
        selected_data = fortinet_data.loc[fortinet_data["Model"] == model]
        columns_to_compare = FORTINET_COLS
    elif vendor == "Palo Alto":
        selected_data = paloalto_data.loc[paloalto_data["Model"] == model]
        columns_to_compare = PALOALTO_COLS
    elif vendor == "SonicWall":
        selected_data = sonicwall_data.loc[sonicwall_data["Model"] == model]
        columns_to_compare = SONICWALL_COLS
    else:
        return "❌ No valid vendor selected.", None

    if selected_data.empty:
        return "❌ Model not found in the dataset.", None

    selected_row = selected_data.iloc[0]

    if manual:
        chosen_model = sophos_data.loc[sophos_data["Model"] == chosen_sophos]
        if chosen_model.empty:
            return "❌ Selected Sophos model not found.", None
        chosen_model = chosen_model.iloc[0]
    else:
        matching_sophos = sophos_data[(sophos_data[columns_to_compare] >= selected_row[columns_to_compare]).any(axis=1)]
        if matching_sophos.empty:
            return f"⚠️ No Sophos model found for {model}. Please contact StarLink Presales Consultant.", None
        chosen_model = matching_sophos.loc[matching_sophos["Firewall Throughput (Gbps)"].idxmin()]

    comparison_table = build_matching_table(selected_row, chosen_model, columns_to_compare)
    return f"✅ Best matching Sophos model for **{model}**: **{chosen_model['Model']}**", comparison_table

# 🔹 Gradio UI
def update_model_list(vendor):
    models = get_models(vendor)
    return gr.update(choices=models, value=models[0] if models else None)

with gr.Blocks() as app:
    gr.Markdown("## 🔥 Firewall Comparison Tool <span style='font-size: 14px;'>V 2.0</span>", elem_id="title")
    gr.Markdown("<hr>", elem_id="divider")

    vendor_dropdown = gr.Dropdown(
        choices=["Fortinet", "Palo Alto", "SonicWall"],
        label="📌 Select a Vendor",
        value="Fortinet"
    )
    model_dropdown = gr.Dropdown(choices=get_models("Fortinet"), label="📌 Select a Model", value=get_models("Fortinet")[0])
    
    vendor_dropdown.change(fn=update_model_list, inputs=vendor_dropdown, outputs=model_dropdown)

    manual_select = gr.Checkbox(label="🔍 Manually select Sophos model?")
    sophos_dropdown = gr.Dropdown(choices=sophos_data["Model"].dropna().unique().tolist(), label="📌 Choose a Sophos Model", visible=False)

    def toggle_sophos_dropdown(manual):
        return gr.update(visible=manual)

    manual_select.change(fn=toggle_sophos_dropdown, inputs=manual_select, outputs=sophos_dropdown)

    compare_button = gr.Button("Compare")
    result_text = gr.Markdown("")
    result_table = gr.Dataframe()

    compare_button.click(fn=compare_models, inputs=[vendor_dropdown, model_dropdown, manual_select, sophos_dropdown], outputs=[result_text, result_table])

    gr.Markdown("<div class='footer'>Developed by <b>Rajeesh - rajeesh@starlinkme.net</b></div>", elem_id="footer")

app.launch(server_name="0.0.0.0")
