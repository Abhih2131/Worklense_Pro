
import streamlit as st
import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import base64
from io import BytesIO
from theme_handler import selected_theme
from utils.formatting import format_in_indian_style

# === Load Report Style ===
with open("utils/report_style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

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

    df["date_of_joining"] = pd.to_datetime(df["date_of_joining"], errors="coerce")
    df["date_of_exit"] = pd.to_datetime(df["date_of_exit"], errors="coerce")

    st.markdown("<h2 style='text-align: left;'>Attrition Snapshot</h2>", unsafe_allow_html=True)

    df_exits = df[
        (df["date_of_exit"] >= pd.to_datetime("2025-04-01")) &
        (df["date_of_exit"] <= pd.to_datetime("2026-03-31"))
    ].copy()

    opening_hc = df[
        (df["date_of_joining"] <= pd.to_datetime("2025-04-01")) &
        ((df["date_of_exit"].isna()) | (df["date_of_exit"] > pd.to_datetime("2025-04-01")))
    ].shape[0]

    closing_hc = df[
        (df["date_of_joining"] <= pd.to_datetime("2026-03-31")) &
        ((df["date_of_exit"].isna()) | (df["date_of_exit"] > pd.to_datetime("2026-03-31")))
    ].shape[0]

    avg_hc = (opening_hc + closing_hc) / 2 if (opening_hc + closing_hc) > 0 else 1

    total_exits = df_exits.shape[0]
    attrition_pct = (total_exits / avg_hc) * 100 if avg_hc > 0 else 0
    regrettable_pct = df_exits[df_exits["exit_type"].str.lower() == "regrettable"].shape[0] / avg_hc * 100
    non_regrettable_pct = df_exits[df_exits["exit_type"].str.lower() == "non-regrettable"].shape[0] / avg_hc * 100
    retirement_pct = df_exits[df_exits["exit_type"].str.lower() == "retirement"].shape[0] / avg_hc * 100

    df_exits["exit_tenure"] = ((pd.to_datetime(df_exits["date_of_exit"]) - pd.to_datetime(df_exits["date_of_joining"])) / pd.Timedelta(days=365.25)).round(1)
    avg_tenure_exited = df_exits["exit_tenure"].mean()

    top_exit_region = df_exits["zone"].mode()[0] if not df_exits["zone"].dropna().empty else "N/A"
    high_perf_attrition_pct = df_exits[df_exits["rating_25"].str.lower() == "excellent"].shape[0] / avg_hc * 100
    top_talent_attrition_pct = df_exits[df_exits["top_talent"].str.lower() == "yes"].shape[0] / avg_hc * 100

    col1, col2, col3, col4 = st.columns(4)
    with col1: st.markdown(kpi("Total Attrition % (FY)", f"{attrition_pct:.1f}%"), unsafe_allow_html=True)
    with col2: st.markdown(kpi("Regrettable Attrition %", f"{regrettable_pct:.1f}%"), unsafe_allow_html=True)
    with col3: st.markdown(kpi("Non-Regret Attrition %", f"{non_regrettable_pct:.1f}%"), unsafe_allow_html=True)
    with col4: st.markdown(kpi("Retirement Attrition %", f"{retirement_pct:.1f}%"), unsafe_allow_html=True)

    col5, col6, col7, col8 = st.columns(4)
    with col5: st.markdown(kpi("Avg Tenure of Exited", f"{avg_tenure_exited:.1f} yrs"), unsafe_allow_html=True)
    with col6: st.markdown(kpi("Top Exit Region", top_exit_region), unsafe_allow_html=True)
    with col7: st.markdown(kpi("High Perf. Attrition %", f"{high_perf_attrition_pct:.1f}%"), unsafe_allow_html=True)
    with col8: st.markdown(kpi("Top Talent Attrition %", f"{top_talent_attrition_pct:.1f}%"), unsafe_allow_html=True)

    # Chart logic reused
    df_exits["exit_tenure"] = (
        (pd.to_datetime(df_exits["date_of_exit"]) - pd.to_datetime(df_exits["date_of_joining"])) / pd.Timedelta(days=365.25)
    ).round(1)

    df_exits["fy_exit"] = df_exits["date_of_exit"].dt.year.apply(lambda y: f"FY-{y+1}")

    # Row 1
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 📉 Attrition Trend")
        trend_data = df[df["date_of_exit"].notna()].copy()
        trend_data["fy"] = trend_data["date_of_exit"].dt.year.apply(lambda y: f"FY-{y+1}")
        allowed_fy = [f"FY-{y}" for y in range(2022, 2027)]
        trend_summary = (
            trend_data["fy"]
            .value_counts()
            .reindex(allowed_fy, fill_value=0)
            .reset_index()
        )
        trend_summary.columns = ["FY", "Exits"]
        fig1 = px.bar(trend_summary, x="FY", y="Exits", text="Exits")
        fig1.update_traces(textposition="outside")
        fig1.update_layout(height=400, yaxis_range=[0, trend_summary["Exits"].max() * 1.2])
        st.plotly_chart(fig1, use_container_width=True)
    with col2:
        st.markdown("### 🧾 Attrition by Exit Type")
        exit_type_summary = df_exits["exit_type"].value_counts().reset_index()
        exit_type_summary.columns = ["Exit Type", "Count"]
        fig2 = px.pie(exit_type_summary, names="Exit Type", values="Count", hole=0.3)
        fig2.update_layout(height=400)
        st.plotly_chart(fig2, use_container_width=True)

    # Row 2
    col3, col4 = st.columns(2)
    with col3:
        st.markdown("### ⏳ Tenure of Exited Employees")
        bins = [0, 1, 3, 5, 10, float("inf")]
        labels = ["<1", "1–3", "3–5", "5–10", "10+"]
        df_exits["Tenure Bucket"] = pd.cut(df_exits["exit_tenure"], bins=bins, labels=labels, right=False)
        tenure_summary = df_exits["Tenure Bucket"].value_counts().reindex(labels).reset_index()
        tenure_summary.columns = ["Bucket", "Count"]
        fig3 = px.bar(tenure_summary, x="Bucket", y="Count", text="Count")
        fig3.update_traces(textposition="outside")
        fig3.update_layout(height=400, yaxis_range=[0, tenure_summary["Count"].max() * 1.2])
        st.plotly_chart(fig3, use_container_width=True)
    with col4:
        st.markdown("### 👥 Attrition by Gender")
        gender_summary = df_exits["gender"].str.title().value_counts().reset_index()
        gender_summary.columns = ["Gender", "Count"]
        fig4 = px.pie(gender_summary, names="Gender", values="Count")
        fig4.update_layout(height=400)
        st.plotly_chart(fig4, use_container_width=True)

    # Row 3
    col5, col6 = st.columns(2)
    with col5:
        st.markdown("### 🧾 Attrition by Rating (FY)")
        rating_summary = df_exits["rating_25"].value_counts().reset_index()
        rating_summary.columns = ["Rating", "Count"]
        fig5 = px.bar(rating_summary, x="Rating", y="Count", text="Count")
        fig5.update_traces(textposition="outside")
        fig5.update_layout(height=400, yaxis_range=[0, rating_summary["Count"].max() * 1.2])
        st.plotly_chart(fig5, use_container_width=True)
    with col6:
        st.markdown("### 🔎 Exit Reason Distribution")
        reason_summary = df_exits["reason_for_exit"].value_counts().reset_index()
        reason_summary.columns = ["Reason", "Count"]
        fig6 = px.pie(reason_summary, names="Reason", values="Count", hole=0.4)
        fig6.update_layout(height=400)
        st.plotly_chart(fig6, use_container_width=True)

    # Row 4
    col7, col8 = st.columns(2)
    with col7:
        st.markdown("### 🧠 Skill Loss")
        skill_text = " ".join(df_exits[["skills_1", "skills_2", "skills_3"]].astype(str).stack().dropna().str.lower().tolist())
        wc1 = WordCloud(width=800, height=400, background_color="white").generate(skill_text)
        buf1 = BytesIO(); plt.figure(figsize=(6,3)); plt.imshow(wc1); plt.axis("off"); plt.tight_layout(); plt.savefig(buf1, format="png"); buf1.seek(0)
        img1 = base64.b64encode(buf1.read()).decode("utf-8")
        st.markdown(f'<img src="data:image/png;base64,{img1}" width="100%">', unsafe_allow_html=True)

    with col8:
        st.markdown("### 🧭 Competency Loss")
        comp_text = " ".join(df_exits["competency"].dropna().astype(str).str.lower().tolist())
        wc2 = WordCloud(width=800, height=400, background_color="white").generate(comp_text)
        buf2 = BytesIO(); plt.figure(figsize=(6,3)); plt.imshow(wc2); plt.axis("off"); plt.tight_layout(); plt.savefig(buf2, format="png"); buf2.seek(0)
        img2 = base64.b64encode(buf2.read()).decode("utf-8")
        st.markdown(f'<img src="data:image/png;base64,{img2}" width="100%">', unsafe_allow_html=True)


    # === Excel Download Section ===
    from pandas import ExcelWriter

    download_data = {
        "Attrition Trend": trend_summary,
        "Exit Type": exit_type_summary,
        "Tenure Buckets": tenure_summary,
        "Gender": gender_summary,
        "Ratings": rating_summary,
        "Exit Reasons": reason_summary,
        "Skills": pd.DataFrame({"Skills": skill_text.split()}),
        "Competencies": pd.DataFrame({"Competencies": comp_text.split()})
    }

    def prepare_download_excel(data_dict):
        output = BytesIO()
        with ExcelWriter(output, engine="xlsxwriter") as writer:
            for sheet, data in data_dict.items():
                data.to_excel(writer, sheet_name=sheet[:31], index=False)
        output.seek(0)
        return output.read()

    excel_data = prepare_download_excel(download_data)
    with st.expander("📥 Download Chart Data (Excel)"):
        st.download_button("Download All Chart Data", data=excel_data, file_name="Attrition_Charts.xlsx")
