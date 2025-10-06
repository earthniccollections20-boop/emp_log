import streamlit as st
import pandas as pd
import os
from datetime import datetime

# ==============================
# 1. Load employee master data
# ==============================
EMP_FILE = "employees.xlsx"
ATTENDANCE_FILE = "attendance.csv"

# Load employee master list
if os.path.exists(EMP_FILE):
    employees = pd.read_excel(EMP_FILE)
    employees = employees.astype(str)  # ensure consistent string type
else:
    st.error(f"Employee master file {EMP_FILE} not found!")
    st.stop()

# ==============================
# 2. Attendance logging function
# ==============================
def log_attendance(emp_id, name, action):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = pd.DataFrame(
        [[emp_id, name, action, timestamp]],
        columns=["EmpID", "Name", "Action", "Timestamp"]
    )

    # Append to CSV
    if os.path.exists(ATTENDANCE_FILE):
        log_entry.to_csv(ATTENDANCE_FILE, mode="a", header=False, index=False)
    else:
        log_entry.to_csv(ATTENDANCE_FILE, mode="w", header=True, index=False)

    st.success(f"{action} recorded for {name} at {timestamp}")

# ==============================
# 3. UI
# ==============================
st.title("🕒 Office Attendance Tracker")

# Employee input
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
# 4. Attendance summary
# ==============================
st.subheader("📊 Attendance Summary")

if os.path.exists(ATTENDANCE_FILE):
    df = pd.read_csv(ATTENDANCE_FILE)
    df["Timestamp"] = pd.to_datetime(df["Timestamp"])
    df["Date"] = df["Timestamp"].dt.date

    # Daily summary
    st.markdown("### Today's Attendance")
    today = datetime.now().date()
    today_logs = df[df["Date"] == today]
    st.dataframe(today_logs)

    # Weekly summary
    st.markdown("### Weekly Summary (Hours Worked)")
    df["Week"] = df["Timestamp"].dt.strftime("%Y-%U")
    summary = []

    for (emp, week), group in df.groupby(["EmpID", "Week"]):
        checkins = group[group["Action"] == "Check In"]["Timestamp"]
        checkouts = group[group["Action"] == "Check Out"]["Timestamp"]

        if not checkins.empty and not checkouts.empty:
            hours = (checkouts.max() - checkins.min()).total_seconds() / 3600
        else:
            hours = 0

        summary.append([emp, group["Name"].iloc[0], week, round(hours, 2)])

    summary_df = pd.DataFrame(summary, columns=["EmpID", "Name", "Week", "Hours Worked"])
    st.dataframe(summary_df)
else:
    st.info("No attendance logs yet.")
