import pandas as pd
import gradio as gr

# ✅ Use GitHub Raw URLs for Faster CSV Loading
CSV_PATHS = {
    "Fortinet": "https://raw.githubusercontent.com/rajeesh668/firewall-comparison-tool/main/Fortinet%20FW%20Models.csv",
    "Palo Alto": "https://raw.githubusercontent.com/rajeesh668/firewall-comparison-tool/main/PaloAlto%20Spec.csv",
    "SonicWall": "https://raw.githubusercontent.com/rajeesh668/firewall-comparison-tool/main/SonicWall%20Spec.csv",
    "Sophos": "https://raw.githubusercontent.com/rajeesh668/firewall-comparison-tool/main/Sophos_XGS_All_Models_Performance.csv"
}

# ✅ Function to Load CSVs from GitHub
def load_csv_data(file_url, vendor_name):
    try:
        return pd.read_csv(file_url)
    except Exception as e:
        print(f"❌ Could not load {vendor_name} data: {e}")
        return pd.DataFrame()

# ✅ Load Data
fortinet_data = load_csv_data(CSV_PATHS["Fortinet"], "Fortinet")
paloalto_data = load_csv_data(CSV_PATHS["Palo Alto"], "Palo Alto")
sonicwall_data = load_csv_data(CSV_PATHS["SonicWall"], "SonicWall")
sophos_data = load_csv_data(CSV_PATHS["Sophos"], "Sophos")

# ✅ Check If Data is Loaded
print("🔄 Fortinet Data Loaded:", fortinet_data.head())
print("🔄 Palo Alto Data Loaded:", paloalto_data.head())
print("🔄 SonicWall Data Loaded:", sonicwall_data.head())
print("🔄 Sophos Data Loaded:", sophos_data.head())

# ✅ Function to Get Available Models
def get_models(vendor):
    if vendor == "Fortinet":
        return fortinet_data["Model"].dropna().unique().tolist()
    elif vendor == "Palo Alto":
        return paloalto_data["Model"].dropna().unique().tolist()
    elif vendor == "SonicWall":
        return sonicwall_data["Model"].dropna().unique().tolist()
    return []

# ✅ Function to Compare Models
def compare_models(vendor, model):
    return f"🔥 Comparing **{model}** from **{vendor}** with Sophos models."

# ✅ Gradio UI
with gr.Blocks() as app:
    gr.Markdown("## 🔥 Firewall Comparison Tool <span style='font-size: 14px;'>V 2.0</span>", elem_id="title")
    gr.Markdown("<hr>", elem_id="divider")

    vendor_dropdown = gr.Dropdown(["Fortinet", "Palo Alto", "SonicWall"], label="📌 Select a Vendor")
    model_dropdown = gr.Dropdown([], label="📌 Select a Model")
    
    def update_models(vendor):
        return gr.update(choices=get_models(vendor))

    vendor_dropdown.change(update_models, inputs=vendor_dropdown, outputs=model_dropdown)
    
    compare_button = gr.Button("Compare")
    result = gr.Markdown()
    compare_button.click(compare_models, inputs=[vendor_dropdown, model_dropdown], outputs=result)

    gr.Markdown("<div class='footer'>Developed by <b>Rajeesh - rajeesh@starlinkme.net</b></div>", elem_id="footer")

app.launch(server_name="0.0.0.0", server_port=7860)
