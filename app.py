import streamlit as st
import pandas as pd
import os
from datetime import datetime
import pytz
from io import BytesIO

# ==============================
# Config
# ==============================
st.set_page_config(page_title="MK Law Attendance Tracker", layout="wide")

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

employees = employees.astype(str)

# ==============================
# Timezone setup
# ==============================
CST = pytz.timezone("America/Chicago")

# ==============================
# Attendance logging
# ==============================
def log_attendance(emp_id, name, action):
    now_cst = datetime.now(CST)
    iso_time = now_cst.isoformat()
    log_entry = pd.DataFrame(
        [[emp_id, name, action, iso_time]],
        columns=["EmpID", "Name", "Action", "Timestamp"]
    )
    log_entry.to_csv(ATTENDANCE_FILE, mode="a", header=not os.path.exists(ATTENDANCE_FILE), index=False)
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
# Worktime calculation helper
# ==============================
def calculate_worktime(checkins, checkouts):
    total = pd.Timedelta(0)
    i, j = 0, 0
    while i < len(checkins) and j < len(checkouts):
        if checkouts[j] > checkins[i]:
            total += (checkouts[j] - checkins[i])
            i += 1
            j += 1
        else:
            j += 1
    return total

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
# Admin Access
# ==============================
st.sidebar.subheader("🔒 Admin Login")
admin_pass = st.sidebar.text_input("Enter Admin Password", type="password")

if admin_pass == "mysecretpassword":   # 🔑 change this password
    st.subheader("📊 Attendance Summary (CST/CDT)")

    if os.path.exists(ATTENDANCE_FILE):
        df = pd.read_csv(ATTENDANCE_FILE)

        # Always reload fresh data
        df = df.copy()

        # Parse timestamps
        df["Timestamp"] = pd.to_datetime(df["Timestamp"], utc=True, errors="coerce")
        df = df.dropna(subset=["Timestamp"])
        df["Timestamp"] = df["Timestamp"].dt.tz_convert("America/Chicago")
        df["Date"] = df["Timestamp"].dt.strftime("%m/%d/%y")
        df["Time"] = df["Timestamp"].dt.strftime("%I:%M:%S %p")
        df["Month"] = df["Timestamp"].dt.strftime("%Y-%m")

        # ---- Daily Summary ----
        st.markdown("### 📅 Daily Attendance Summary")
        day_filter = st.date_input("Select a date", datetime.now(CST).date())
        day_str = day_filter.strftime("%m/%d/%y")
        day_logs = df[df["Date"] == day_str]

        if not day_logs.empty:
            daily_summary = []
            for emp, group in day_logs.groupby("EmpID"):
                emp_name = group["Name"].iloc[0]
                checkins = group.loc[group["Action"] == "Check In", "Timestamp"].sort_values().tolist()
                checkouts = group.loc[group["Action"] == "Check Out", "Timestamp"].sort_values().tolist()

                total_work = calculate_worktime(checkins, checkouts)

                total_secs = int(total_work.total_seconds())
                hours, remainder = divmod(total_secs, 3600)
                minutes, seconds = divmod(remainder, 60)
                work_time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

                first_in = checkins[0].strftime("%I:%M %p") if checkins else "-"
                last_out = checkouts[-1].strftime("%I:%M %p") if checkouts else "-"

                daily_summary.append([emp, emp_name, day_str, first_in, last_out, work_time_str])

            daily_df = pd.DataFrame(
                daily_summary,
                columns=["EmpID", "Name", "Date", "First Check-In", "Last Check-Out", "Hours Worked (HH:MM:SS)"]
            )
            st.dataframe(daily_df)

            st.download_button(
                "⬇️ Download Daily Summary (Excel)",
                data=to_excel(daily_df),
                file_name=f"daily_summary_{day_str}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.info(f"No attendance logs for {day_str}.")

        # ---- Monthly Summary ----
        st.markdown("### 📅 Monthly Attendance Summary")
        month_filter = st.selectbox("Select a month", sorted(df["Month"].unique(), reverse=True))
        month_logs = df[df["Month"] == month_filter]

        if not month_logs.empty:
            monthly_summary = []
            for emp, group in month_logs.groupby("EmpID"):
                emp_name = group["Name"].iloc[0]
                checkins = group.loc[group["Action"] == "Check In", "Timestamp"].sort_values().tolist()
                checkouts = group.loc[group["Action"] == "Check Out", "Timestamp"].sort_values().tolist()

                total_work = calculate_worktime(checkins, checkouts)

                total_secs = int(total_work.total_seconds())
                hours, remainder = divmod(total_secs, 3600)
                minutes, seconds = divmod(remainder, 60)
                work_time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

                monthly_summary.append([emp, emp_name, month_filter, work_time_str])

            monthly_df = pd.DataFrame(
                monthly_summary,
                columns=["EmpID", "Name", "Month", "Hours Worked (HH:MM:SS)"]
            )
            st.dataframe(monthly_df)

            st.download_button(
                "⬇️ Download Monthly Summary (Excel)",
                data=to_excel(monthly_df),
                file_name=f"monthly_summary_{month_filter}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.info(f"No logs found for {month_filter}.")
    else:
        st.info("No attendance logs yet.")

elif admin_pass !=_
