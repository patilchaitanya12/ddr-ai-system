import streamlit as st
import requests

BACKEND_URL = "http://127.0.0.1:8000/ddr/generate"

st.set_page_config(page_title="DDR AI System", layout="wide")

st.title("DDR AI Report Generator")

st.markdown("Upload inspection and thermal reports to generate a structured DDR.")

# File upload
inspection_file = st.file_uploader("Upload Inspection Report (PDF)", type=["pdf"])
thermal_file = st.file_uploader("Upload Thermal Report (PDF)", type=["pdf"])

if st.button("🚀 Generate DDR Report"):

    if not inspection_file or not thermal_file:
        st.error("Please upload both files.")
    else:
        with st.spinner("Processing..."):

            files = {
                "inspection_file": (inspection_file.name, inspection_file, "application/pdf"),
                "thermal_file": (thermal_file.name, thermal_file, "application/pdf"),
            }

            try:
                response = requests.post(BACKEND_URL, files=files)

                if response.status_code == 200:
                    data = response.json()["data"]

                    st.success("DDR Report Generated!")

                    #Property Summary
                    st.subheader("Property Issue Summary")
                    for item in data.get("property_issue_summary", []):
                        st.write(f"- {item}")

                    #Area Observations
                    st.subheader("Area-wise Observations")
                    for area in data.get("area_wise_observations", []):
                        st.markdown(f"**{area['area'].capitalize()}**")
                        st.write(area["details"])

                    #Severity
                    st.subheader("Severity Assessment")
                    for s in data.get("severity_assessment", []):
                        st.write(f"{s['area'].capitalize()}: {s['severity']} → {s['reason']}")

                    #Root Causes
                    st.subheader("Probable Root Causes")
                    for cause in data.get("probable_root_cause", []):
                        st.write(f"- {cause}")

                    #Recommendations
                    st.subheader("Recommended Actions")
                    for action in data.get("recommended_actions", []):
                        st.write(f"- {action}")

                    #Missing Info
                    st.subheader("Missing / Unclear Information")
                    for m in data.get("missing_or_unclear_information", []):
                        st.write(f"- {m}")

                    #Additional Notes
                    if data.get("additional_notes"):
                        st.subheader("Additional Notes")
                        for note in data.get("additional_notes", []):
                            st.write(f"- {note}")

                else:
                    st.error(f"Error: {response.text}")

            except Exception as e:
                st.error(f"Failed to connect to backend: {e}")