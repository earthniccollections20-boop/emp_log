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
    iso_time = now_cst.isoformat()  # stored cleanly
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

# Utility: Convert dataframe to Excel
def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Sheet1")
    processed_data = output.getvalue()
    return processed_data

if admin_pass == "mysecretpassword":   # 🔑 change this password
    st.subheader("📊 Attendance Summary (CST/CDT)")

    if os.path.exists(ATTENDANCE_FILE):
        df = pd.read_csv(ATTENDANCE_FILE)

        # Parse timestamps from ISO
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
                emp_name = group["Name"].iloc[0]
                checkins = group[group["Action"] == "Check In"]["Timestamp"].sort_values().tolist()
                checkouts = group[group["Action"] == "Check Out"]["Timestamp"].sort_values().tolist()

                # Calculate total worked time
                total_work = pd.Timedelta(0)
                for i in range(min(len(checkins), len(checkouts))):
                    total_work += (checkouts[i] - checkins[i])

                total_secs = int(total_work.total_seconds())
                hours, remainder = divmod(total_secs, 3600)
                minutes, seconds = divmod(remainder, 60)
                work_time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

                first_in = checkins[0].strftime("%I:%M %p") if checkins else "-"
                last_out = checkouts[-1].strftime("%I:%M %p") if checkouts else "-"

                daily_summary.append([
                    emp,
                    emp_name,
                    today,
                    first_in,
                    last_out,
                    work_time_str
                ])

            daily_df = pd.DataFrame(
                daily_summary,
                columns=["EmpID", "Name", "Date", "First Check-In", "Last Check-Out", "Hours Worked (HH:MM:SS)"]
            )
            st.dataframe(daily_df)

            # Download daily summary
            st.download_button(
                label="⬇️ Download Daily Summary (Excel)",
                data=to_excel(daily_df),
                file_name=f"daily_summary_{today}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.info("No attendance logs for today.")

        # ---- Monthly Summary ----
        st.markdown("### Monthly Summary (Hours Worked)")
        df["Month"] = df["Timestamp"].dt.strftime("%Y-%m")  # Year-Month
        monthly_summary = []

        for (emp, month), group in df.groupby(["EmpID", "Month"]):
            emp_name = group["Name"].iloc[0]
            checkins = group[group["Action"] == "Check In"]["Timestamp"].sort_values().tolist()
            checkouts = group[group["Action"] == "Check Out"]["Timestamp"].sort_values().tolist()

            total_work = pd.Timedelta(0)
            for i in range(min(len(checkins), len(checkouts))):
                total_work += (checkouts[i] - checkins[i])

            total_secs = int(total_work.total_seconds())
            hours, remainder = divmod(total_secs, 3600)
            minutes, seconds = divmod(remainder, 60)
            work_time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

            monthly_summary.append([emp, emp_name, month, work_time_str])

        monthly_df = pd.DataFrame(monthly_summary, columns=["EmpID", "Name", "Month", "Hours Worked (HH:MM:SS)"])
        st.dataframe(monthly_df)

        # Download monthly summary
        st.download_button(
            label="⬇️ Download Monthly Summary (Excel)",
            data=to_excel(monthly_df),
            file_name="monthly_summary.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    else:
        st.info("No attendance logs yet.")

elif admin_pass != "":
    st.sidebar.error("❌ Wrong password! Access denied.")
