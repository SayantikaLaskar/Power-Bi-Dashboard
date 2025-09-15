import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import glob

# ---------------------------
# 1. LOAD DATA
# ---------------------------
# Read all CSVs in the Orders folder
orders_files = glob.glob("Orders/*.csv")  # make sure you use correct path
orders_list = [pd.read_csv(f) for f in orders_files]
orders = pd.concat(orders_list, ignore_index=True)

# Read Returns and People
returns = pd.read_excel("Returns.xlsx")
people = pd.read_excel("People.xlsx")

# Merge datasets
data = orders.merge(returns, on="Order ID", how="left")
data = data.merge(people, on="Region", how="left")

# Convert date
data['Order Date'] = pd.to_datetime(data['Order Date'])
data['Year'] = data['Order Date'].dt.year
data['Month'] = data['Order Date'].dt.month
data['Month_Year'] = data['Order Date'].dt.to_period('M')

# ---------------------------
# 2. SIDEBAR FILTERS
# ---------------------------
st.sidebar.title("Filters")
selected_region = st.sidebar.multiselect("Select Region", options=data['Region'].unique(), default=data['Region'].unique())
selected_employee = st.sidebar.multiselect("Select Employee", options=data['Person'].unique(), default=data['Person'].unique())
selected_year = st.sidebar.multiselect("Select Year", options=data['Year'].unique(), default=data['Year'].unique())

filtered_data = data[
    (data['Region'].isin(selected_region)) &
    (data['Person'].isin(selected_employee)) &
    (data['Year'].isin(selected_year))
]

# ---------------------------
# 3. METRICS
# ---------------------------
total_orders = filtered_data['Order ID'].nunique()
return_count = filtered_data[filtered_data['Returned'] == "Yes"]['Order ID'].nunique()
return_rate = return_count / total_orders if total_orders > 0 else 0
avg_return_value = filtered_data.loc[filtered_data['Returned'] == "Yes", "Sales"].mean()

# Top 5 Employees by Returns
top5_employees = (
    filtered_data[filtered_data['Returned'] == "Yes"]
    .groupby("Person")['Order ID']
    .count()
    .nlargest(5)
)

# Monthly Return Trend
monthly_returns = (
    filtered_data[filtered_data['Returned'] == "Yes"]
    .groupby("Month_Year")['Order ID']
    .count()
)

# ---------------------------
# 4. DASHBOARD LAYOUT
# ---------------------------
st.title("📊 Returns Analysis Dashboard")

# KPI Cards
col1, col2, col3 = st.columns(3)
col1.metric("Total Orders", total_orders)
col2.metric("Return Count", return_count)
col3.metric("Return Rate", f"{return_rate:.2%}")
col1.metric("Avg Return Value", f"${avg_return_value:.2f}")

# ---------------------------
# 5. VISUALIZATIONS
# ---------------------------
# Monthly Returns Trend
st.subheader("Monthly Return Trend")
fig, ax = plt.subplots(figsize=(10,5))
monthly_returns.plot(ax=ax, label="Monthly Returns", marker='o')
if len(monthly_returns) > 12:
    monthly_returns.shift(12).plot(ax=ax, label="Last Year Returns", linestyle='--', marker='o')
ax.set_ylabel("Return Count")
ax.set_xlabel("Month-Year")
ax.legend()
st.pyplot(fig)

# Top 5 Employees Bar Chart
st.subheader("Top 5 Employees by Returns")
fig2, ax2 = plt.subplots(figsize=(8,5))
sns.barplot(x=top5_employees.index, y=top5_employees.values, palette="viridis", ax=ax2)
ax2.set_ylabel("Return Count")
ax2.set_xlabel("Employee")
st.pyplot(fig2)

# Employee Contribution Pie Chart
st.subheader("Employee Contribution to Total Returns")
employee_contrib = filtered_data[filtered_data['Returned'] == "Yes"].groupby("Person")['Order ID'].count()
employee_contrib = employee_contrib / employee_contrib.sum()
fig3, ax3 = plt.subplots(figsize=(6,6))
employee_contrib.plot(kind="pie", autopct="%1.1f%%", ax=ax3)
ax3.set_ylabel("")
st.pyplot(fig3)

# Data Table
st.subheader("Filtered Data Table")
st.dataframe(filtered_data)
