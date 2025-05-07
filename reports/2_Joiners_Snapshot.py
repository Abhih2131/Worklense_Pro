
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import base64
from io import BytesIO
from theme_handler import selected_theme
from utils.formatting import format_in_indian_style
from pandas import ExcelWriter

# === Load Report Style ===
with open("utils/report_style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# === KPI Card Formatter ===
def kpi(label, value):
    return f"""
    <div class="kpi-card">
        <div class="kpi-value">{value}</div>
        <div class="kpi-label">{label}</div>
    </div>
    """

# === Word Cloud ===
def generate_wordcloud(data):
    text = ' '.join(data.dropna().astype(str).tolist())
    wordcloud = WordCloud(width=800, height=400, background_color='white').generate(text)
    buffer = BytesIO()
    plt.figure(figsize=(6, 3))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis("off")
    plt.tight_layout()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    img_str = base64.b64encode(buffer.read()).decode()
    plt.close()
    return f'<img src="data:image/png;base64,{img_str}" width="100%">'

def render(data_frames):
    selected_theme()

    df = data_frames.get("employee", pd.DataFrame())
    if df.empty:
        st.warning("Employee data not available.")
        return

    today = pd.to_datetime("2025-04-30")
    fy_start = pd.to_datetime("2025-04-01")
    fy_end = pd.to_datetime("2026-03-31")

    df["date_of_joining"] = pd.to_datetime(df["date_of_joining"], errors="coerce")
    df["date_of_birth"] = pd.to_datetime(df["date_of_birth"], errors="coerce")
    df["total_exp_yrs"] = pd.to_numeric(df["total_exp_yrs"], errors="coerce")
    df["total_ctc_pa"] = pd.to_numeric(df["total_ctc_pa"], errors="coerce")

    df_joiners = df[(df["date_of_joining"] >= fy_start) & (df["date_of_joining"] <= fy_end)].copy()
    df_joiners["age"] = ((today - df_joiners["date_of_birth"]).dt.days / 365.25).round(1)

    total_joiners = df_joiners.shape[0]
    avg_age_joiners = df_joiners["age"].mean()
    avg_experience_joiners = df_joiners["total_exp_yrs"].mean()
    avg_ctc_joiners = df_joiners["total_ctc_pa"].mean() / 1e5
    percentage_freshers = df_joiners[df_joiners["total_exp_yrs"] < 1].shape[0] / total_joiners * 100 if total_joiners > 0 else 0

    male_count = df_joiners[df_joiners["gender"].str.lower() == "male"].shape[0]
    female_count = df_joiners[df_joiners["gender"].str.lower() == "female"].shape[0]
    gender_ratio = f"{male_count}:{female_count}" if female_count != 0 else "All Male"

    top_source = df_joiners["hiring_source"].mode()[0] if not df_joiners["hiring_source"].dropna().empty else "N/A"
    top_zone = df_joiners["zone"].mode()[0] if not df_joiners["zone"].dropna().empty else "N/A"

    st.markdown("<h2 style='text-align: left;'>New Joinee Snapshot</h2>", unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)
    with col1: st.markdown(kpi("Total New Joiners", format_in_indian_style(total_joiners)), unsafe_allow_html=True)
    with col2: st.markdown(kpi("Average Age", f"{avg_age_joiners:.1f} yrs"), unsafe_allow_html=True)
    with col3: st.markdown(kpi("Average Experience", f"{avg_experience_joiners:.1f} yrs"), unsafe_allow_html=True)
    with col4: st.markdown(kpi("Average CTC", f"₹ {avg_ctc_joiners:.1f} L"), unsafe_allow_html=True)

    col5, col6, col7, col8 = st.columns(4)
    with col5: st.markdown(kpi("Percentage of Freshers", f"{percentage_freshers:.1f}%"), unsafe_allow_html=True)
    with col6: st.markdown(kpi("Male to Female Ratio", gender_ratio), unsafe_allow_html=True)
    with col7: st.markdown(kpi("Top Hiring Source", top_source), unsafe_allow_html=True)
    with col8: st.markdown(kpi("Top Hiring Zone", top_zone), unsafe_allow_html=True)

    # === Chart Data Prep ===
    hiring_source_summary = df_joiners['hiring_source'].value_counts().reset_index()
    hiring_source_summary.columns = ['Source', 'Count']

    qualification_summary = df_joiners['highest_qualification'].value_counts().reset_index()
    qualification_summary.columns = ['Qualification', 'Count']

    gender_summary = df_joiners['gender'].str.title().value_counts().reset_index()
    gender_summary.columns = ['Gender', 'Count']

    sector_summary = df_joiners['employment_sector'].value_counts().reset_index()
    sector_summary.columns = ['Sector', 'Count']

    exp_bins = [0, 1, 3, 5, 10, float('inf')]
    exp_labels = ['<1 Yr', '1–3 Yrs', '3–5 Yrs', '5–10 Yrs', '10+ Yrs']
    df_joiners['Exp Range'] = pd.cut(df_joiners['total_exp_yrs'], bins=exp_bins, labels=exp_labels, right=False)
    exp_summary = df_joiners['Exp Range'].value_counts().reindex(exp_labels).reset_index()
    exp_summary.columns = ['Experience Range', 'Count']

    job_roles = df_joiners['unique_job_role'].dropna().astype(str)

    # === Charts ===
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 📌 Hiring Source Distribution")
        fig1 = px.pie(hiring_source_summary, names='Source', values='Count', hole=0.4)
        fig1.update_layout(height=400)
        st.plotly_chart(fig1, use_container_width=True)
    with col2:
        st.markdown("### 🎓 Qualification Distribution")
        fig2 = px.pie(qualification_summary, names='Qualification', values='Count', hole=0.4)
        fig2.update_layout(height=400)
        st.plotly_chart(fig2, use_container_width=True)

    col3, col4 = st.columns(2)
    with col3:
        st.markdown("### 👥 Gender Split of Joiners")
        fig3 = px.pie(gender_summary, names='Gender', values='Count')
        fig3.update_layout(height=400)
        st.plotly_chart(fig3, use_container_width=True)
    with col4:
        st.markdown("### 🏢 Employment Sector Distribution")
        fig4 = px.bar(sector_summary, x='Sector', y='Count', text='Count')
        fig4.update_traces(textposition='outside')
        fig4.update_layout(height=400, yaxis_range=[0, sector_summary['Count'].max() * 1.2])
        st.plotly_chart(fig4, use_container_width=True)

    col5, col6 = st.columns(2)
    with col5:
        st.markdown("### 🧭 Experience Range of Joiners")
        fig5 = px.bar(exp_summary, x='Experience Range', y='Count', text='Count')
        fig5.update_traces(textposition='outside')
        fig5.update_layout(height=400, yaxis_range=[0, exp_summary['Count'].max() * 1.2])
        st.plotly_chart(fig5, use_container_width=True)
    with col6:
        st.markdown("### 🧠 Unique Job Roles Hired")
        st.markdown(generate_wordcloud(job_roles), unsafe_allow_html=True)

    # === Excel Download ===
    download_data = {
        "Hiring Source": hiring_source_summary,
        "Qualification": qualification_summary,
        "Gender Split": gender_summary,
        "Employment Sector": sector_summary,
        "Experience Range": exp_summary,
        "Job Roles": pd.DataFrame({'Job Roles': job_roles})
    }

    def prepare_download_excel(data_dict):
        output = BytesIO()
        with ExcelWriter(output, engine="xlsxwriter") as writer:
            for sheet_name, df_sheet in data_dict.items():
                df_sheet.to_excel(writer, sheet_name=sheet_name[:31], index=False)
        output.seek(0)
        return output.read()

    excel_file = prepare_download_excel(download_data)
    with st.expander("📥 Download Chart Data (Excel)"):
        st.download_button("Download All Chart Data", data=excel_file, file_name="Joiners_Charts.xlsx")
