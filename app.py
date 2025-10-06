import streamlit as st
import pandas as pd
import os
from datetime import datetime
import pytz
from io import BytesIO

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
CST = pytz.timezone("America/Chicago")

# ==============================
# Attendance logging
# ==============================
def log_attendance(emp_id, name, action):
    now_cst = datetime.now(CST)
    iso_time = now_cst.isoformat()  # stored cleanly in UTC offset
    log_entry = pd.DataFrame(
        [[emp_id, name, action, iso_time]],
        columns=["EmpID", "Name", "Action", "Timestamp"]
    )

    if os.path.exists(ATTENDANCE_FILE):
        log_entry.to_csv(ATTENDANCE_FILE, mode="a", header=False, index=False)
    else:
        log_entry.to_csv(ATTENDANCE_FILE, mode="w", header=True, index=False)

    st.success(f"{action} recorded for {name} at {now_cst.strftime('%m/%d/%y %I:%M:%S %p')} CST/CDT")

# ==============================
# Excel export helper
# ==============================
def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Sheet1")
    return output.getvalue()

# ==============================
# Streamlit UI
# ==============================
st.title("⚖️ MK Law Attendance Tracker")

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
# Admin Access (Password Protected)
# ==============================
st.sidebar.subheader("🔒 Admin Login")
admin_pass = st.sidebar.text_input("Enter Admin Password", type="password")

if admin_pass == "mysecretpassword":   # 🔑 change this password
    st.subheader("📊 Attendance Summary (CST/CDT)")

    if os.path.exists(ATTENDANCE_FILE):
        df = pd.read_csv(ATTENDANCE_FILE)

        # Parse timestamps properly
        df["Timestamp"] = pd.to_datetime(df["Timestamp"], utc=True, errors="coerce")
        df = df.dropna(subset=["Timestamp"])

        # Convert to CST/CDT for display
        df["Timestamp"] = df["Timestamp"].dt.tz_convert("America/Chicago")
        df["Date"] = df["Timestamp"].dt.strftime("%m/%d/%y")
        df["Time"] = df["Timestamp"].dt.strftime("%I:%M:%S %p")

        # ---- Daily Summary ----
        st.markdown("### Today's Attendance Summary")
        today = datetime.now(CST).strftime("%m/%d/%y")
        today_logs = df[df["Date"] == today]

        if not today_logs.empty:
            daily_summary = []
            for emp, group in today_logs.groupby("EmpID"):
                emp_name = group["Name"].iloc[0]
                checkins = group[group["Action"] == "Check In"]["Timestamp"].sort_values().toli_
