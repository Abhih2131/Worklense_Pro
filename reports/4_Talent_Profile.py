def render(data_frames):
    import streamlit as st
    import pandas as pd
    import os
    from datetime import datetime
    from PIL import Image, ImageDraw, ImageOps
    import base64
    from io import BytesIO
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    import time

    def format_inr(val):
        try:
            return f"₹ {round(val / 100000, 2)} Lakhs"
        except:
            return "-"

    def format_date(val):
        try:
            return pd.to_datetime(val).strftime("%d-%b-%Y")
        except:
            return "-"

    def create_circular_image(path, size=(150, 150)):
        img = Image.open(path).convert("RGBA").resize(size)
        mask = Image.new("L", size, 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0) + size, fill=255)
        output = ImageOps.fit(img, size, centering=(0.5, 0.5))
        output.putalpha(mask)
        return output

    def get_circular_image_b64(empid):
        for ext in [".png", ".jpg", ".jpeg"]:
            path = f"data/images/{empid}{ext}"
            if os.path.exists(path):
                img = create_circular_image(path)
                buffer = BytesIO()
                img.save(buffer, format="PNG")
                return f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode()}"
        return ""

    def export_html_to_pdf_using_cdp(html_path, pdf_path):
        chrome_options = Options()
        chrome_options.add_argument('--headless=new')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--window-size=1280,1696')

        driver = webdriver.Chrome(options=chrome_options)
        driver.get("file://" + os.path.abspath(html_path))
        time.sleep(2)

        result = driver.execute_cdp_cmd("Page.printToPDF", {
            "landscape": False,
            "printBackground": True,
            "preferCSSPageSize": True
        })

        with open(pdf_path, "wb") as f:
            f.write(base64.b64decode(result['data']))

        driver.quit()

    df = data_frames.get("employee", pd.DataFrame())
    if df.empty:
        st.warning("Employee data not available.")
        return

    today = pd.to_datetime("today")
    df["date_of_exit"] = pd.to_datetime(df["date_of_exit"], errors="coerce")
    df["date_of_joining"] = pd.to_datetime(df["date_of_joining"], errors="coerce")
    df["last_promotion"] = pd.to_datetime(df["last_promotion"], errors="coerce")
    df["last_transfer"] = pd.to_datetime(df["last_transfer"], errors="coerce")
    df["date_of_birth"] = pd.to_datetime(df["date_of_birth"], errors="coerce")

    df_active = df[df["date_of_exit"].isna() | (df["date_of_exit"] > today)]

    st.markdown("### 🔍 Talent Profile Summary")
    emp_id = st.text_input("Enter Employee ID", key="pdf_input")

    if not emp_id:
        return

    try:
        emp_id = int(emp_id)
    except:
        st.error("Employee ID must be numeric.")
        return

    row = df_active[df_active["employee_id"] == emp_id]
    if row.empty:
        st.warning("No active employee found.")
        return

    emp = row.iloc[0]
    photo_b64 = get_circular_image_b64(emp["employee_id"])

    age = "-"
    tenure = "-"
    if pd.notna(emp["date_of_birth"]):
        age = int((today - emp["date_of_birth"]).days / 365.25)
        age = f"{age} yrs"
    if pd.notna(emp["date_of_joining"]):
        delta = today - emp["date_of_joining"]
        years = delta.days // 365
        months = (delta.days % 365) // 30
        tenure = f"{years} yrs {months} months" if years > 0 else f"{months} months"

    def section(title, fields):
        merged_skills = ', '.join(filter(None, [
            str(emp.get('skills_1', '')).strip(),
            str(emp.get('skills_2', '')).strip(),
            str(emp.get('skills_3', '')).strip()
        ])) or "-"

        merged_competency = "-"
        if emp.get("competency_type") or emp.get("competency_level"):
            merged_competency = " - ".join(
                filter(None, [str(emp.get("competency_type", "")).strip(), str(emp.get("competency_level", "")).strip()])
            ) or "-"

        s = f'<div class="section"><h4>{title}</h4>'
        for label, key in fields:
            val = emp.get(key, "-")
            if key == "merged_skills":
                val = merged_skills
            if key == "merged_competency":
                val = merged_competency
            if "ctc" in key and pd.notna(val):
                val = format_inr(val)
            elif any(x in key for x in ["date", "promotion", "transfer"]) and pd.notna(val):
                val = format_date(val)
            elif "training" in key and pd.notna(val):
                val = f"{val} hrs"
            elif "exp" in key and pd.notna(val) and isinstance(val, (int, float)):
                val = f"{val} yrs"
            s += f'<div class="row"><div class="label">{label}</div><div class="value">{val}</div></div>'
        s += '</div>'
        return s

    html = f"""
    <html><head><meta charset='utf-8'>
    <style>
    body {{ font-family: 'Segoe UI', sans-serif; font-size: 13px; margin: 20px; background: #f5f8fc; }}
    .profile-header {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        background: #0E2A47;
        color: white;
        padding: 20px;
        border-radius: 12px;
        margin-top: 20px;
    }}
    .profile-info {{
        flex-grow: 1;
    }}
    .profile-info h2 {{
        margin: 0;
        font-size: 22px;
    }}
    .photo {{
        width: 120px;
        height: 120px;
        border-radius: 50%;
        border: 3px solid white;
        object-fit: cover;
    }}
    .gridbox {{ display: grid; grid-template-columns: 1fr 1fr; gap: 30px; margin-top: 30px; }}
    .section {{ padding: 15px 20px; background: #ffffff; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); font-size: 13px; }}
    .section h4 {{ margin-bottom: 10px; color: #0E2A47; border-bottom: 1px solid #e0e0e0; padding-bottom: 5px; }}
    .row {{ display: flex; justify-content: space-between; border-bottom: 1px solid #f0f0f0; padding: 4px 0; }}
    .label {{ font-weight: bold; color: #555; }}
    .value {{ color: #000; }}
    </style></head><body>

    <div class="profile-header">
        <div class="profile-info">
            <h2>{emp['employee_name']}</h2>
            <div>Employee ID: <b>{emp['employee_id']}</b></div>
            <div>{emp['function']} | {emp['department']} | Band: {emp['band']} | Grade: {emp['grade']}</div>
            <div>Age: {age} | Tenure: {tenure}</div>
        </div>
        {f"<img src='{photo_b64}' class='photo'/>" if photo_b64 else ''}
    </div>
    """

    html += "<div class='gridbox'>" + section("Organizational Context", [
        ("Company", "company"), ("Business Unit", "business_unit"),
        ("Department", "department"), ("Function", "function"),
        ("Zone", "zone"), ("Cluster", "cluster"), ("Area", "area"), ("Location", "location")
    ]) + section("Tenure & Movement", [
        ("Date of Joining", "date_of_joining"), ("Last Promotion", "last_promotion"),
        ("Last Transfer", "last_transfer"), ("Total Experience", "total_exp_yrs"),
        ("Previous Experience", "prev_exp_in_yrs"), ("Employment Type", "employment_type")
    ]) + "</div>"

    html += "<div class='gridbox'>" + section("Compensation", [
        ("Fixed CTC", "fixed_ctc_pa"), ("Variable CTC", "variable_ctc_pa"),
        ("Total CTC", "total_ctc_pa")
    ]) + section("Performance & Potential", [
        ("Satisfaction Score", "satisfaction_score"), ("Engagement Score", "engagement_score"),
        ("Rating 2025", "rating_25"), ("Rating 2024", "rating_24"),
        ("Top Talent", "Top Talent"), ("Succession Ready", "succession_ready")
    ]) + "</div>"

    html += "<div class='gridbox'>" + section("Development & Learning", [
        ("Learning Program", "learning_program"), ("Training Hours", "training_hours")
    ]) + section("Competency & Skills", [
        ("Competency", "competency"), ("Competency Details", "merged_competency"), ("Skills", "merged_skills")
    ]) + "</div>"

    html += "<div class='gridbox'>" + section("Education & Background", [
        ("Qualification", "qualification"), ("Highest Qualification", "highest_qualification"),
        ("Qualification Type", "qualification_type"), ("Previous Employers", "previous_employers"),
        ("Last Employer", "last_employer"), ("Employment Sector", "employment_sector")
    ]) + "</div></body></html>"

    st.components.v1.html(html, height=1000, scrolling=True)

    os.makedirs("exports", exist_ok=True)
    html_path = os.path.join("exports", f"profile_{emp['employee_id']}.html")
    pdf_path = os.path.join("exports", f"profile_{emp['employee_id']}.pdf")

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)

    export_html_to_pdf_using_cdp(html_path, pdf_path)

    with open(pdf_path, "rb") as f:
        st.download_button("⬇️ Download as PDF", f, file_name=os.path.basename(pdf_path))
