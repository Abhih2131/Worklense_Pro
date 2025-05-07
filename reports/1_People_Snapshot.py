import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from theme_handler import selected_theme
from utils.formatting import format_in_indian_style

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
    df["date_of_exit"] = pd.to_datetime(df["date_of_exit"], errors="coerce")
    df["date_of_birth"] = pd.to_datetime(df["date_of_birth"], errors="coerce")
    df["last_promotion"] = pd.to_datetime(df["last_promotion"], errors="coerce")

    df_active = df[(df["date_of_exit"].isna()) | (df["date_of_exit"] > today)]
    df_active["age"] = ((today - df_active["date_of_birth"]).dt.days / 365.25).astype(int)
    df_active["tenure"] = ((today - df_active["date_of_joining"]).dt.days / 365.25)

    # === KPIs ===
    total_employees = df_active.shape[0]
    new_hires = df[df["date_of_joining"].between(fy_start, fy_end)].shape[0]
    total_exits = df[df["date_of_exit"].between(fy_start, fy_end)].shape[0]
    avg_age = int(df_active["age"].mean())
    avg_tenure = round(df_active["tenure"].mean(), 1)
    avg_exp = round(df_active["total_exp_yrs"].fillna(0).mean(), 1)
    training_hours = int(df_active["training_hours"].fillna(0).sum())
    satisfaction_score = round(df_active["satisfaction_score"].fillna(0).mean(), 1)

    st.markdown("<h2 style='text-align: left;'>People: Snapshot</h2>", unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)
    with col1: st.markdown(kpi("Total Employees", f"{total_employees:,}"), unsafe_allow_html=True)
    with col2: st.markdown(kpi("New Hires (FY)", f"{new_hires:,}"), unsafe_allow_html=True)
    with col3: st.markdown(kpi("Total Exits (FY)", f"{total_exits:,}"), unsafe_allow_html=True)
    with col4: st.markdown(kpi("Average Age", f"{avg_age} Yrs"), unsafe_allow_html=True)

    col5, col6, col7, col8 = st.columns(4)
    with col5: st.markdown(kpi("Average Tenure", f"{avg_tenure} Yrs"), unsafe_allow_html=True)
    with col6: st.markdown(kpi("Average Experience", f"{avg_exp} Yrs"), unsafe_allow_html=True)
    with col7: st.markdown(kpi("Training Hours", f"{training_hours:,}"), unsafe_allow_html=True)
    with col8: st.markdown(kpi("Avg Satisfaction Score", f"{satisfaction_score}"), unsafe_allow_html=True)

    # === Charts Data ===
    headcount, cost_data, attr_data = [], [], []
    for yr in range(2021, 2026):
        start = pd.to_datetime(f"{yr}-04-01")
        end = pd.to_datetime(f"{yr+1}-03-31")
        active = df[(df["date_of_joining"] <= end) & ((df["date_of_exit"].isna()) | (df["date_of_exit"] > end))]
        headcount.append({"FY": f"FY-{yr+1}", "Headcount": active.shape[0]})
        total_ctc = active["total_ctc_pa"].fillna(0).sum()
        cost_data.append({"FY": f"FY-{yr+1}", "Total CTC": total_ctc / 1e7})
        exits = df[df["date_of_exit"].between(start, end)].shape[0]
        opening = df[(df["date_of_joining"] <= start) & ((df["date_of_exit"].isna()) | (df["date_of_exit"] > start))].shape[0]
        closing = df[(df["date_of_joining"] <= end) & ((df["date_of_exit"].isna()) | (df["date_of_exit"] > end))].shape[0]
        avg_hc = (opening + closing) / 2 if (opening + closing) > 0 else 1
        rate = round((exits / avg_hc) * 100, 1)
        attr_data.append({"FY": f"FY-{yr+1}", "Attrition %": rate})

    df_hc = pd.DataFrame(headcount)
    df_cost = pd.DataFrame(cost_data)
    df_attr = pd.DataFrame(attr_data)

    gender_counts = df_active["gender"].fillna("Unknown").str.title().value_counts().reset_index()
    gender_counts.columns = ["Gender", "Count"]

    age_bins = [0, 20, 25, 30, 35, 40, 45, 50, 55, 60, float("inf")]
    age_labels = ["<20", "20-24", "25-29", "30-34", "35-39", "40-44", "45-49", "50-54", "55-59", "60+"]
    df_active["Age Group"] = pd.cut(df_active["age"], bins=age_bins, labels=age_labels, right=False)
    age_counts = df_active["Age Group"].value_counts().reindex(age_labels, fill_value=0).reset_index()
    age_counts.columns = ["Age Group", "Count"]

    bins = [0, 0.5, 1, 3, 5, 10, float("inf")]
    labels = ["0–6 Months", "6–12 Months", "1–3 Years", "3–5 Years", "5–10 Years", "10+ Years"]
    df_active["Tenure Group"] = pd.cut(df_active["tenure"], bins=bins, labels=labels, right=False)
    tenure_counts = df_active["Tenure Group"].value_counts().reindex(labels, fill_value=0).reset_index()
    tenure_counts.columns = ["Tenure", "Count"]

    # === Charts ===
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 👥 Manpower Growth")
        fig1 = px.line(df_hc, x="FY", y="Headcount", markers=True, text="Headcount")
        fig1.update_traces(textposition="top center")
        fig1.update_layout(height=400, yaxis_range=[0, df_hc["Headcount"].max() * 1.2])
        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        st.markdown("### 💰 Manpower Cost")
        df_cost["Rounded CTC"] = df_cost["Total CTC"].round(1)
        fig2 = px.bar(df_cost, x="FY", y="Total CTC", text="Rounded CTC", labels={"Total CTC": "INR Cr"})
        fig2.update_traces(textposition="outside")
        fig2.update_layout(height=400, yaxis_range=[0, df_cost["Total CTC"].max() * 1.2])
        st.plotly_chart(fig2, use_container_width=True)

    col3, col4 = st.columns(2)
    with col3:
        st.markdown("### 📉 Attrition Trend")
        fig3 = px.bar(df_attr, x="FY", y="Attrition %", text="Attrition %")
        fig3.update_traces(textposition="outside")
        fig3.update_layout(height=400, yaxis_range=[0, df_attr["Attrition %"].max() * 1.2])
        st.plotly_chart(fig3, use_container_width=True)

    with col4:
        st.markdown("### 🌐 Gender Diversity")
        fig4 = px.pie(gender_counts, names="Gender", values="Count", hole=0.3)
        fig4.update_layout(height=400)
        st.plotly_chart(fig4, use_container_width=True)

    col5, col6 = st.columns(2)
    with col5:
        st.markdown("### 🎂 Age Distribution")
        fig5 = px.bar(age_counts, x="Age Group", y="Count", text="Count")
        fig5.update_traces(textposition="outside")
        fig5.update_layout(height=400, yaxis_range=[0, age_counts["Count"].max() * 1.2])
        st.plotly_chart(fig5, use_container_width=True)

    with col6:
        st.markdown("### ⏳ Tenure Distribution")
        fig6 = px.bar(tenure_counts, x="Tenure", y="Count", text="Count")
        fig6.update_traces(textposition="outside")
        fig6.update_layout(height=400, yaxis_range=[0, tenure_counts["Count"].max() * 1.2])
        st.plotly_chart(fig6, use_container_width=True)

    # === Excel Download ===
    import io
    from pandas import ExcelWriter

    download_data = {
        "Manpower Growth": df_hc,
        "Manpower Cost": df_cost,
        "Attrition Trend": df_attr,
        "Gender Diversity": gender_counts,
        "Age Distribution": age_counts,
        "Tenure Distribution": tenure_counts
    }

    def prepare_download_excel(data_dict):
        output = io.BytesIO()
        with ExcelWriter(output, engine="xlsxwriter") as writer:
            for sheet_name, df_sheet in data_dict.items():
                df_sheet.to_excel(writer, sheet_name=sheet_name[:31], index=False)
        output.seek(0)
        return output.read()

    excel_file = prepare_download_excel(download_data)
    with st.expander("📥 Download Chart Data (Excel)"):
        st.download_button("Download All Chart Data", data=excel_file, file_name="Diversity_Charts.xlsx")
