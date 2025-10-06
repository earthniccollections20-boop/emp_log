import streamlit as st
import pandas as pd
import os
from datetime import datetime
import pytz

# ==============================
# File Paths
# ==============================
EMP_EXCEL = "employees.xlsx"
EMP_CSV = "employees.csv"
ATTENDANCE_FILE = "attendance.csv"

# ==============================
# Load Employee Master
# ==============================
if os.path.exists(EMP_EXCEL):
    employees = pd.read_excel(EMP_EXCEL, engine="openpyxl")
elif os.path.exists(EMP_CSV):
    employees = pd.read_csv(EMP_CSV)
else:
    st.error("❌ No employee master file found! Upload employees.xlsx or employees.csv")
    st.stop()

employees = employees.astype(str)  # Ensure consistent format

# ==============================
# Timezone setup
# ==============================
CST = pytz.timezone("America/Chicago")  # Explicit CST/CDT timezone

# ==============================
# Attendance logging
# ==============================
def log_attendance(emp_id, name, action):
    now_cst = datetime.now(pytz.utc).astimezone(CST)  # system time converted to CST
    timestamp = now_cst.strftime("%m/%d/%y %I:%M:%S %p")  # mm/dd/yy 12hr format
    log_entry = pd.DataFrame(
        [[emp_id, name, action, timestamp]],
        columns=["EmpID", "Name", "Action", "Timestamp"]
    )

    if os.path.exists(ATTENDANCE_FILE):
        log_entry.to_csv(ATTENDANCE_FILE, mode="a", header=False, index=False)
    else:
        log_entry.to_csv(ATTENDANCE_FILE, mode="w", header=True, index=False)

    st.success(f"{action} recorded for {name} at {timestamp} CST")

# ==============================
# Streamlit UI
# ==============================
st.title("🕒 Office Attendance Tracker (CST)")

emp_id = st.text_input("Enter Employee ID")
name = st.text_input("Enter Name")

col1, col2 = st.columns(2)
with col1:
    if st.button("Check In"):
        if ((employees['EmpID'] == emp_id) & (employees['Name'] == name)).any():
            log_attendance(emp_id, name, "Check In")
        else:
            st.error("❌ Invalid Employee ID or Name")

with col2:
    if st.button("Check Out"):
        if ((employees['EmpID'] == emp_id) & (employees['Name'] == name)).any():
            log_attendance(emp_id, name, "Check Out")
        else:
            st.error("❌ Invalid Employee ID or Name")

# ==============================
# Attendance Summary
# ==============================
st.subheader("📊 Attendance Summary (CST)")

if os.path.exists(ATTENDANCE_FILE):
    df = pd.read_csv(ATTENDANCE_FILE)

    # Flexible timestamp parsing
    df["Timestamp"] = pd.to_datetime(df["Timestamp"], errors="coerce")
    df = df.dropna(subset=["Timestamp"])  

    df["Date"] = df["Timestamp"].dt.strftime("%m/%d/%y")
    df["Time"] = df["Timestamp"].dt.strftime("%I:%M:%S %p")

    # ---- Daily Summary ----
    st.markdown("### Today's Attendance Summary")
    to
