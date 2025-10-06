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
CST = pytz.timezone("US/Central")

# ==============================
# Attendance logging
# ==============================
def log_attendance(emp_id, name, action):
    now_cst = datetime.now(pytz.utc).astimezone(CST)  # convert to CST
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
st.title("🕒 Office Attendance Tracker")

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
st.subheader("📊 Attendance Summary")

if os.path.exists(ATTENDANCE_FILE):
    df = pd.read_csv(ATTENDANCE_FILE)

    # Flexible timestamp parsing
    df["Timestamp"] = pd.to_datetime(df["Timestamp"], errors="coerce")
    df = df.dropna(subset=["Timestamp"])  

    df["Date"] = df["Timestamp"].dt.strftime("%m/%d/%y")
    df["Time"] = df["Timestamp"].dt.strftime("%I:%M:%S %p")

    # ---- Daily Summary ----
    st.markdown("### Today's Attendance Summary")
    today = datetime.now(CST).strftime("%m/%d/%y")
    today_logs = df[df["Date"] == today]

    if not today_logs.empty:
        daily_summary = []
        for emp, group in today_logs.groupby("EmpID"):
            checkins = group[group["Action"] == "Check In"]["Timestamp"]
            checkouts = group[group["Action"] == "Check Out"]["Timestamp"]

            first_in = checkins.min().strftime("%I:%M:%S %p") if not checkins.empty else "-"
            last_out = checkouts.max().strftime("%I:%M:%S %p") if not checkouts.empty else "-"

            if not checkins.empty and not checkouts.empty:
                work_time = checkouts.max() - checkins.min()
                work_time_str = str(work_time)  # H:M:S
            else:
                work_time_str = "0:00:00"

            daily_summary.append([
                emp,
                group["Name"].iloc[0],
                today,
                first_in,
                last_out,
                work_time_str
            ])

        daily_df = pd.DataFrame(
            daily_summary,
            columns=["EmpID", "Name", "Date", "First Check-In", "Last Check-Out", "Hours Worked"]
        )
        st.dataframe(daily_df)
    else:
        st.info("No attendance logs for today.")

    # ---- Monthly Summary ----
    st.markdown("### Monthly Summary (Hours Worked)")
    df["Month"] = df["Timestamp"].dt.strftime("%Y-%m")  # Year-Month
    monthly_summary = []

    for (emp, month), group in df.groupby(["EmpID", "Month"]):
        checkins = group[group["Action"] == "Check In"]["Timestamp"]
        checkouts = group[group["Action"] == "Check Out"]["Timestamp"]

        if not checkins.empty and not checkouts.empty:
            work_time = checkouts.max() - checkins.min()
            work_time_str = str(work_time)
        else:
            work_time_str = "0:00:00"

        monthly_summary.append([emp, group["Name"].iloc[0], month, work_time_str])

    monthly_df = pd.DataFrame(monthly_summary, columns=["EmpID", "Name", "Month", "Hours Worked"])
    st.dataframe(monthly_df)

else:
    st.info("No attendance logs yet.")
