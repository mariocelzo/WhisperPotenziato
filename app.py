import streamlit as st
import whisper
from fpdf import FPDF
import os
import tempfile
from datetime import datetime
from pathlib import Path
import time
import psutil

# Setup
desktop = str(Path.home() / "Desktop")
output_folder = os.path.join(desktop, "trascrizioni")
os.makedirs(output_folder, exist_ok=True)

st.set_page_config(page_title="Batch Trascrizione Audio", page_icon="🎧")
st.title("🎧 Batch Trascrizione Audio in PDF (con Whisper)")
st.markdown("Trascina **uno o più file audio**, li trascriveremo uno per uno.")

def log_temperature(log_path):
    try:
        temp = os.popen("osx-cpu-temp").read().strip()
    except Exception:
        temp = "N/A"
    with open(log_path, "a") as f:
        f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')},{temp}\n")

# Caricamento multiplo
uploaded_files = st.file_uploader("Carica file audio", type=["m4a", "mp3", "wav"], accept_multiple_files=True)

if uploaded_files:
    st.info(f"Hai caricato {len(uploaded_files)} file. La trascrizione inizierà uno per uno.")

    progress_bar = st.progress(0)
    status_text = st.empty()

    model = whisper.load_model("small")

    temp_log_path = os.path.join(output_folder, "temperature_log.csv")
    with open(temp_log_path, "w") as f:
        f.write("Timestamp,CPU_Temp\n")

    for i, uploaded_file in enumerate(uploaded_files):
        file_name = uploaded_file.name
        now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        base_filename = f"{file_name.rsplit('.',1)[0]}_{now}"
        txt_path = os.path.join(output_folder, f"{base_filename}.txt")
        pdf_path = os.path.join(output_folder, f"{base_filename}.pdf")

        status_text.info(f"🎙️ [{i+1}/{len(uploaded_files)}] Trascrivo: `{file_name}`...")

        log_temperature(temp_log_path)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".m4a") as tmp:
            tmp.write(uploaded_file.read())
            tmp_path = tmp.name

        result = model.transcribe(tmp_path)
        text = result["text"]

        with open(txt_path, "w") as f:
            f.write(text)

        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_font("ArialUnicode", "", "fonts/Arial Unicode.ttf", uni=True)
        pdf.set_font("ArialUnicode", size=12)
        pdf.multi_cell(0, 10, text)
        pdf.output(pdf_path)

        status_text.success(f"✅ Completato: {file_name}")

        os.remove(tmp_path)
        progress_bar.progress((i + 1) / len(uploaded_files))
        st.markdown(f"📄 [Scarica PDF {file_name}]({pdf_path})")

        log_temperature(temp_log_path)
        time.sleep(300)

    status_text.success("✅ Tutti i file sono stati elaborati.")
    st.success("🎉 Tutte le trascrizioni sono state completate!")

    # Storico file
    st.subheader("📂 Storico trascrizioni")

    files = sorted(Path(output_folder).glob("*"), reverse=True)
    for f in files:
        with open(f, "rb") as file_data:
            st.download_button(f"📄 {f.name}", file_data, file_name=f.name)

else:
    st.warning("📂 Trascina uno o più file audio per iniziare.")