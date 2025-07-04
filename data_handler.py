import pandas as pd
from datetime import datetime, date
import os

def load_employee_data(file_path):
    """Load and clean employee master data with safe column handling."""
    df = pd.read_excel(file_path)
    df.columns = df.columns.str.strip().str.lower()
    df.fillna("", inplace=True)

    # Convert dates if columns exist
    if 'date_of_birth' in df.columns:
        df['date_of_birth'] = pd.to_datetime(df['date_of_birth'], errors='coerce')
        df['age'] = df['date_of_birth'].apply(lambda dob: calculate_age(dob))
    if 'date_of_joining' in df.columns:
        df['date_of_joining'] = pd.to_datetime(df['date_of_joining'], errors='coerce')
        df['tenure'] = df['date_of_joining'].apply(lambda doj: calculate_tenure(doj))
    if 'date_of_exit' in df.columns:
        df['date_of_exit'] = pd.to_datetime(df['date_of_exit'], errors='coerce')

    return df

def load_leave_data(file_path):
    """Load HRMS leave data."""
    df = pd.read_excel(file_path)
    df.columns = df.columns.str.strip().str.lower()
    df.fillna("", inplace=True)
    return df

def load_sales_data(file_path):
    """Load sales INR data."""
    df = pd.read_excel(file_path)
    df.columns = df.columns.str.strip().str.lower()
    df.fillna("", inplace=True)
    return df

def calculate_age(dob):
    if pd.isnull(dob): return None
    today = date.today()
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

def calculate_tenure(doj):
    if pd.isnull(doj): return None
    today = date.today()
    return round((pd.Timestamp(today) - doj).days / 365, 2)

def load_all_data(folder_path):
    """Load all key datasets into a dictionary."""
    try:
        # Compose full paths
        emp_file = os.path.join(folder_path, "employee_master.xlsx")
        leave_file = os.path.join(folder_path, "HRMS_Leave.xlsx")
        sales_file = os.path.join(folder_path, "Sales_INR.xlsx")

        # Check if files exist (helpful debug for cloud!)
        for f in [emp_file, leave_file, sales_file]:
            if not os.path.exists(f):
                import streamlit as st
                st.error(f"File not found: {f}")
                raise FileNotFoundError(f"File not found: {f}")

        data = {
            "employee": load_employee_data(emp_file),
            "leave": load_leave_data(leave_file),
            "sales": load_sales_data(sales_file)
        }
        return data
    except Exception as e:
        import streamlit as st
        st.error(f"Data loading failed: {str(e)}")
        raise RuntimeError(f"Data loading failed: {str(e)}")
