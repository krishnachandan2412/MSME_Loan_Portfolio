
from datetime import datetime
import io
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


# PAGE CONFIG


st.set_page_config(
    page_title="MSME Loan Portfolio Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)



# METRICS

def calculate_metrics(df: pd.DataFrame) -> dict:
    total = len(df)
    metrics = {
        "total_customers": total,
        "regular_customers": int((df["status"] == "Regular").sum()),
        "monitored_customers": int((df["status"] == "Monitored").sum()),
        "upcoming_npa_customers": int((df["status"] == "Upcoming_NPA").sum()),
        "current_npa_customers": int((df["status"] == "Current_NPA").sum()),
        "unclassified_customers": int((df["status"] == "Unclassified").sum()),
    }

    metrics["current_npa_pct"] = (
        metrics["current_npa_customers"] / total * 100 if total else 0.0
    )
    metrics["upcoming_npa_pct"] = (
        metrics["upcoming_npa_customers"] / total * 100 if total else 0.0
    )
    metrics["regular_payer_pct"] = (
        metrics["regular_customers"] / total * 100 if total else 0.0
    )

    metrics["digital_customers"] = int((df["payment_method"] == "Digital").sum())
    metrics["digital_adoption_pct"] = (
        metrics["digital_customers"] / total * 100 if total else 0.0
    )

    metrics["visit_covered_customers"] = int(df["visit_covered"].sum())
    metrics["visit_coverage_pct"] = (
        metrics["visit_covered_customers"] / total * 100 if total else 0.0
    )

    metrics["total_loan_amount"] = float(df["loan_amount"].sum()) if total else 0.0
    metrics["avg_loan_amount"] = float(df["loan_amount"].mean()) if total else 0.0

    npa_rate = metrics["current_npa_pct"]
    upcoming_npa_rate = metrics["upcoming_npa_pct"]
    dpd_coverage_eff = metrics["visit_coverage_pct"]
    collection_coverage = metrics["visit_coverage_pct"]

    risk_score = (
        (npa_rate / 100) * 40
        + (upcoming_npa_rate / 100) * 60
        + (100 - dpd_coverage_eff) / 100 * 15
        + (100 - collection_coverage) / 100 * 15
    )
    metrics["risk_score"] = min(max(risk_score, 0), 100)

    return metrics



# PLOTS

def plot_portfolio_composition(df: pd.DataFrame):
    comp = (
        df["segment"]
        .value_counts()
        .reindex(
            ["Healthy", "Monitored", "Upcoming_NPA", "Current_NPA", "Unclassified"],
            fill_value=0,
        )
        .reset_index()
    )
    comp.columns = ["segment", "customers"]
    comp["percentage"] = comp["customers"] / comp["customers"].sum() * 100

    fig = px.bar(
        comp,
        x="segment",
        y="customers",
        text=comp["percentage"].map(lambda x: f"{x:.1f}%"),
        title="Portfolio Composition by Segment",
        labels={"segment": "Segment", "customers": "Customers"},
        color="segment",
        color_discrete_map={
            "Healthy": "#2ecc71",
            "Monitored": "#f1c40f",
            "Upcoming_NPA": "#e67e22",
            "Current_NPA": "#e74c3c",
            "Unclassified": "#95a5a6",
        },
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(height=400, showlegend=False)
    return fig


def plot_risk_zones(df: pd.DataFrame):
    def zone(s):
        if s == "Regular":
            return "Green"
        if s == "Monitored":
            return "Yellow"
        if s == "Upcoming_NPA":
            return "Orange"
        if s == "Current_NPA":
            return "Red"
        return "Unclassified"

    temp = df.copy()
    temp["risk_zone"] = temp["status"].apply(zone)
    agg = temp["risk_zone"].value_counts().reset_index()
    agg.columns = ["risk_zone", "customers"]

    fig = px.pie(
        agg,
        names="risk_zone",
        values="customers",
        title="Risk Zone Distribution",
        color="risk_zone",
        color_discrete_map={
            "Green": "#2ecc71",
            "Yellow": "#f1c40f",
            "Orange": "#e67e22",
            "Red": "#e74c3c",
            "Unclassified": "#95a5a6",
        },
        hole=0.4,
    )
    fig.update_layout(height=400)
    return fig


def plot_profession_repayment(df: pd.DataFrame):
    temp = df.copy()
    temp["paid_flag"] = temp["payment_regular"].astype(int)
    stats = temp.groupby("profession")["paid_flag"].mean().reset_index()
    stats["payment_rate_pct"] = stats["paid_flag"] * 100

    fig = px.bar(
        stats,
        x="profession",
        y="payment_rate_pct",
        title="Repayment Performance by Profession",
        labels={"profession": "Profession", "payment_rate_pct": "Payment Rate (%)"},
        color="payment_rate_pct",
        color_continuous_scale="RdYlGn",
    )
    fig.update_layout(height=400, showlegend=False)
    return fig


def plot_payment_method_mix(df: pd.DataFrame):
    dist = df["payment_method"].value_counts().reset_index()
    dist.columns = ["payment_method", "customers"]
    dist["percentage"] = dist["customers"] / dist["customers"].sum() * 100

    fig = px.bar(
        dist,
        x="payment_method",
        y="customers",
        text=dist["percentage"].map(lambda x: f"{x:.1f}%"),
        title="Payment Method Mix (Cash vs Digital)",
        labels={"payment_method": "Payment Method", "customers": "Customers"},
        color="payment_method",
        color_discrete_map={"Cash": "#e67e22", "Digital": "#3498db"},
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(height=400, showlegend=False)
    return fig


def plot_dpd_distribution(df: pd.DataFrame):
    fig = px.histogram(
        df,
        x="dpd",
        nbins=30,
        title="DPD (Days Past Due) Distribution",
        labels={"dpd": "Days Past Due"},
        color_discrete_sequence=["#9b59b6"],
    )
    fig.update_layout(height=400, yaxis_title="Customers")
    return fig


def plot_emi_vs_loan(df: pd.DataFrame):
    fig = px.scatter(
        df,
        x="paid_emis",
        y="loan_amount",
        color="status",
        size="emi_amount",
        title="EMI Collection vs Loan Amount",
        labels={"paid_emis": "EMIs Paid", "loan_amount": "Loan Amount (₹)"},
        color_discrete_map={
            "Regular": "#2ecc71",
            "Monitored": "#f1c40f",
            "Upcoming_NPA": "#e67e22",
            "Current_NPA": "#e74c3c",
            "Unclassified": "#95a5a6",
        },
    )
    fig.update_layout(height=400)
    return fig


def plot_risk_score_gauge(risk_score: float):
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=risk_score,
            title={"text": "Portfolio Risk Score"},
            domain={"x": [0, 1], "y": [0, 1]},
            gauge={
                "axis": {"range": [0, 100]},
                "bar": {"color": "darkblue"},
                "steps": [
                    {"range": [0, 30], "color": "#2ecc71"},
                    {"range": [30, 60], "color": "#f1c40f"},
                    {"range": [60, 100], "color": "#e74c3c"},
                ],
                "threshold": {
                    "line": {"color": "red", "width": 4},
                    "thickness": 0.75,
                    "value": 47.5,
                },
            },
        )
    )
    fig.update_layout(height=400)
    return fig


def plot_legal_vs_segment(df: pd.DataFrame):
    temp = df.copy()
    temp["segment_group"] = temp["status"].replace(
        {
            "Regular": "Regular",
            "Monitored": "Monitored",
            "Upcoming_NPA": "Upcoming NPA",
            "Current_NPA": "Current NPA",
            "Unclassified": "Unclassified",
        }
    )
    agg = temp.groupby("segment_group")["got_legal_notice"].mean().reset_index()
    agg["legal_notice_pct"] = agg["got_legal_notice"] * 100

    fig = px.bar(
        agg,
        x="segment_group",
        y="legal_notice_pct",
        title="Legal Notice Coverage by Segment",
        labels={"segment_group": "Segment", "legal_notice_pct": "With Legal Notice (%)"},
        color="legal_notice_pct",
        color_continuous_scale="Blues",
    )
    fig.update_layout(height=400, showlegend=False)
    return fig


def plot_visit_coverage(df: pd.DataFrame):
    temp = df.copy()
    temp["segment_group"] = temp["status"].replace(
        {
            "Regular": "Regular",
            "Monitored": "Monitored",
            "Upcoming_NPA": "Upcoming NPA",
            "Current_NPA": "Current NPA",
            "Unclassified": "Unclassified",
        }
    )
    agg = temp.groupby("segment_group")["visit_covered"].mean().reset_index()
    agg["visit_coverage_pct"] = agg["visit_covered"] * 100

    fig = px.bar(
        agg,
        x="segment_group",
        y="visit_coverage_pct",
        title="Collection Visit Coverage by Segment",
        labels={"segment_group": "Segment", "visit_coverage_pct": "Visit Coverage (%)"},
        color="visit_coverage_pct",
        color_continuous_scale="Greens",
    )
    fig.update_layout(height=400, showlegend=False)
    return fig


def plot_irregular_reasons(df: pd.DataFrame):
    temp = df[df["irregular_reason"] != "None"].copy()
    if temp.empty:
        return go.Figure()

    agg = temp["irregular_reason"].value_counts().reset_index()
    agg.columns = ["reason", "cases"]
    agg["percentage"] = agg["cases"] / agg["cases"].sum() * 100

    fig = px.bar(
        agg,
        x="reason",
        y="cases",
        text=agg["percentage"].map(lambda x: f"{x:.1f}%"),
        title="Irregular Payment Reasons",
        labels={"reason": "Reason", "cases": "Number of Cases"},
        color="reason",
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(height=400, showlegend=False)
    return fig



# MAIN

def main():
    st.sidebar.title("📁 Data Source")

    uploaded = st.sidebar.file_uploader(
        "Upload MSME portfolio CSV ",
        type=["csv"],
    )
    st.sidebar.link_button("Download Dataset from GitHub", "https://github.com/your-username/your-repo")
    if uploaded is None:
        st.warning("Please upload a CSV file to view the dashboard.")
        st.stop()

    # Row slider in sidebar
    temp_df = pd.read_csv(uploaded)
    max_rows = len(temp_df)
    row_limit = st.sidebar.slider(
        "Rows to use for analysis",
        min_value=100 if max_rows >= 100 else 1,
        max_value=max_rows,
        value=max_rows,
        step=50 if max_rows >= 150 else 1,
    )
    df = temp_df.head(row_limit)
    st.sidebar.info(f"Using first {row_limit} rows out of {max_rows}")

    metrics = calculate_metrics(df)

    st.title("📊 MSME Loan Portfolio - Executive Dashboard")
    st.write(
        f"Report generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )

    st.subheader("Key Performance Indicators")
    k1, k2, k3, k4, k5, k6, k7 = st.columns(7)
    with k1:
        st.metric("Total Customers", f"{metrics['total_customers']}")
    with k2:
        st.metric("Regular Payers", f"{metrics['regular_payer_pct']:.1f}%")
    with k3:
        st.metric("Current NPA %", f"{metrics['current_npa_pct']:.1f}%")
    with k4:
        st.metric("Upcoming NPA %", f"{metrics['upcoming_npa_pct']:.1f}%")
    with k5:
        st.metric("Visit Coverage", f"{metrics['visit_coverage_pct']:.1f}%")
    with k6:
        st.metric("Digital Adoption", f"{metrics['digital_adoption_pct']:.1f}%")
    with k7:
        st.metric("Risk Score", f"{metrics['risk_score']:.1f}/100")

    st.markdown("---")
    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(plot_portfolio_composition(df), use_container_width=True)
    with c2:
        st.plotly_chart(plot_risk_zones(df), use_container_width=True)

    st.subheader("Profession & Collections")
    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(plot_profession_repayment(df), use_container_width=True)
    with c2:
        st.plotly_chart(plot_payment_method_mix(df), use_container_width=True)

    st.subheader("DPD & Exposure")
    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(plot_dpd_distribution(df), use_container_width=True)
    with c2:
        st.plotly_chart(plot_emi_vs_loan(df), use_container_width=True)

    st.subheader("Legal, Visits & Irregular Reasons")
    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(plot_legal_vs_segment(df), use_container_width=True)
    with c2:
        st.plotly_chart(plot_visit_coverage(df), use_container_width=True)
    st.plotly_chart(plot_irregular_reasons(df), use_container_width=True)

    st.markdown("---")
    st.subheader("Data & Export")

    if st.checkbox("Show raw data", False):
        st.dataframe(df, use_container_width=True, height=350)

    csv_bytes = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download current dataset (CSV)",
        data=csv_bytes,
        file_name=f"msme_portfolio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv",
    )

    # Quick summary at the end
    st.markdown("---")
    st.subheader("Quick Summary")
    st.markdown(
        f"""
- The **portfolio risk score** shows the overall health of the MSME book; higher values mean more stress in NPAs and upcoming NPAs.
- **Current NPA** and **upcoming NPA percentages** highlight how many customers are already defaulted and how many are at high risk of slipping into NPA soon.  
- **Profession-wise payment behavior** compares salaried, self-employed, and business customers so you can see which segment is driving most of the risk  
- **Irregular payment reasons, legal notices, and visit coverage** explain whether problems come from customer stress, fraud/process gaps, or weak collection follow-up.  
- **Payment method mix (cash vs digital)** shows operational risk and audit trail strength, supporting decisions to push more digital collections
"""
    )


if __name__ == "__main__":
    main()



