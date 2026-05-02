import streamlit as st
import requests
from reportlab.platypus import SimpleDocTemplate, Paragraph, Image, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from io import BytesIO

BACKEND_URL = "http://127.0.0.1:8000/ddr/generate"

st.set_page_config(page_title="DDR AI System", layout="wide")
st.title("DDR AI Report Generator")

col1, col2 = st.columns(2)

with col1:
    inspection_file = st.file_uploader("Inspection PDF", type=["pdf"])

with col2:
    thermal_file = st.file_uploader("Thermal PDF", type=["pdf"])

st.divider()


def generate_pdf(data):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("DDR Report", styles["Title"]))
    elements.append(Spacer(1, 20))

    elements.append(Paragraph("Property Issue Summary", styles["Heading2"]))
    for item in data.get("property_issue_summary", []):
        elements.append(Paragraph(f"- {item}", styles["Normal"]))
    elements.append(Spacer(1, 15))

    for area in data.get("area_wise_observations", []):
        elements.append(Paragraph(area["area"].capitalize(), styles["Heading3"]))
        elements.append(Spacer(1, 6))

        elements.append(Paragraph(area.get("details", ""), styles["Normal"]))
        elements.append(Spacer(1, 10))

        for img in area.get("images", []):
            if img:
                try:
                    res = requests.get(img, timeout=5)
                    if res.status_code == 200:
                        elements.append(Image(BytesIO(res.content), width=400, height=250))
                        elements.append(Spacer(1, 10))
                except:
                    continue

        elements.append(Spacer(1, 15))

    elements.append(Paragraph("Severity Assessment", styles["Heading2"]))
    for s in data.get("severity_assessment", []):
        elements.append(
            Paragraph(f"{s['area']}: {s['severity']} → {s['reason']}", styles["Normal"])
        )
    elements.append(Spacer(1, 15))

    elements.append(Paragraph("Probable Root Causes", styles["Heading2"]))
    for c in data.get("probable_root_cause", []):
        elements.append(Paragraph(f"- {c}", styles["Normal"]))
    elements.append(Spacer(1, 15))

    elements.append(Paragraph("Recommended Actions", styles["Heading2"]))
    for a in data.get("recommended_actions", []):
        elements.append(Paragraph(f"- {a}", styles["Normal"]))
    elements.append(Spacer(1, 15))

    elements.append(Paragraph("Missing Information", styles["Heading2"]))
    for m in data.get("missing_or_unclear_information", []):
        elements.append(Paragraph(f"- {m}", styles["Normal"]))
    elements.append(Spacer(1, 15))

    doc.build(elements)
    buffer.seek(0)
    return buffer


if st.button("🚀 Generate DDR Report"):
    if not inspection_file or not thermal_file:
        st.error("Upload both files")
        st.stop()

    progress = st.progress(0)
    status = st.empty()

    try:
        status.info("Uploading files...")
        progress.progress(15)

        files = {
            "inspection_file": (inspection_file.name, inspection_file, "application/pdf"),
            "thermal_file": (thermal_file.name, thermal_file, "application/pdf"),
        }

        status.info("Processing PDFs...")
        progress.progress(40)

        response = requests.post(BACKEND_URL, files=files)

        if response.status_code != 200:
            st.error(response.text)
            st.stop()

        data = response.json()["data"]

        status.info("Generating report...")
        progress.progress(80)

        pdf_buffer = generate_pdf(data)

        progress.progress(100)
        status.success("Report ready")

    except Exception as e:
        st.error(str(e))
        st.stop()

    st.divider()

    st.download_button(
        "📄 Download Report",
        data=pdf_buffer,
        file_name="DDR_Report.pdf"
    )

    st.subheader("Property Issue Summary")
    for item in data.get("property_issue_summary", []):
        st.write(f"- {item}")

    st.subheader("Area-wise Observations")

    for area in data.get("area_wise_observations", []):
        st.markdown(f"### {area['area'].capitalize()}")
        st.write(area.get("details", ""))

        images = area.get("images", [])

        if images:
            cols = st.columns(3)
            for i, img in enumerate(images):
                if img:
                    try:
                        res = requests.get(img, timeout=5)
                        if res.status_code == 200:
                            cols[i % 3].image(res.content, use_container_width=True)
                        else:
                            cols[i % 3].warning("Image failed")
                    except:
                        cols[i % 3].warning("Image not reachable")
                else:
                    cols[i % 3].warning("No image")

        st.markdown("---")

    st.subheader("Severity Assessment")
    for s in data.get("severity_assessment", []):
        st.write(f"{s['area']}: {s['severity']} → {s['reason']}")

    st.subheader("Probable Root Causes")
    for c in data.get("probable_root_cause", []):
        st.write(f"- {c}")

    st.subheader("Recommended Actions")
    for a in data.get("recommended_actions", []):
        st.write(f"- {a}")

    st.subheader("Missing / Unclear Information")
    for m in data.get("missing_or_unclear_information", []):
        st.write(f"- {m}")

    if data.get("additional_notes"):
        st.subheader("Additional Notes")
        for n in data.get("additional_notes", []):
            st.write(f"- {n}")