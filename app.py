"""BusXLaw 5-Year Financial Model — Streamlit dashboard.

Run:  streamlit run app.py
"""
import plotly.graph_objects as go
import streamlit as st

from model import BASE, SCENARIOS, milestones, run_model, scenario

st.set_page_config(page_title="BusXLaw Financial Model", layout="wide")

BLUE, ORANGE, AQUA, YELLOW, RED, GRAY = "#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e34948", "#7a808b"


def money(v):
    a, s = abs(v), "-" if v < 0 else ""
    if a >= 1e6:
        return f"{s}${a / 1e6:.2f}M"
    if a >= 1e3:
        return f"{s}${a / 1e3:.0f}K"
    return f"{s}${a:.0f}"


def style(fig, money_axis=True):
    fig.update_layout(
        height=380, margin=dict(l=10, r=10, t=10, b=10), hovermode="x unified",
        legend=dict(orientation="h", y=-0.15, yanchor="top", x=0, xanchor="left", traceorder="normal",
                    font=dict(size=13)),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
    )
    fig.update_yaxes(gridcolor="rgba(128,128,128,0.2)", zerolinecolor="rgba(128,128,128,0.6)",
                     tickformat="$~s" if money_axis else "~s", automargin=True)
    fig.update_xaxes(automargin=True)
    return fig


def chart(col, fig, title, caption, money_axis=True):
    col.markdown(f"#### {title}")
    col.plotly_chart(style(fig, money_axis), width="stretch")
    col.caption(caption)


# ---------- Sidebar: assumptions ----------
st.sidebar.header("Assumptions")
st.sidebar.caption("Pick a scenario, then fine-tune any lever. None of these numbers has been tested yet.")
name = st.sidebar.radio("Scenario", list(SCENARIOS), index=1, horizontal=True)
preset = SCENARIOS[name]

# Keying each slider on the scenario resets it to that scenario's value when the scenario changes.
demo_mult = st.sidebar.slider("Demo user volume (x base)", 0.4, 1.6, preset["demo_mult"], 0.05, key=f"d{name}",
                              help="Base forecast is 10K demo users in Year 1, rising to 100K in Year 5.")
conv = st.sidebar.slider("Demo-to-paid conversion (%)", 1.0, 10.0, preset["conv"] * 100, 0.5, key=f"c{name}") / 100
churn = st.sidebar.slider("Monthly subscriber churn (%)", 2.0, 12.0, preset["churn"] * 100, 0.5, key=f"ch{name}") / 100
att_mult = st.sidebar.slider("Attorney members (x base)", 0.4, 1.6, preset["att_mult"], 0.05, key=f"a{name}",
                             help="Base is 15 attorneys in Year 1, rising to 120 in Year 5.")
p_starter = st.sidebar.slider("Starter price ($/month)", 15, 49, int(BASE.p_starter), 1)
p_pro = st.sidebar.slider("Pro price ($/month)", 49, 129, int(BASE.p_pro), 1)

a = scenario(name, demo_mult=demo_mult, conv=conv, churn=churn, att_mult=att_mult,
             p_starter=p_starter, p_pro=p_pro)
df = run_model(a)
m = milestones(df)
y1, y5 = df.iloc[0], df.iloc[4]

# ---------- Header ----------
st.caption("TOPIC #21 · MGMT 102 · ADD-ON")
st.title("BusXLaw 5-Year Financial Model")
st.write("An interactive version of our pro forma and unit economics. Base case matches our Excel model. "
         "Team: Jay Goodman, Kyle Johnson, Holden Milne and Xavier Moreira.")

# ---------- KPIs ----------
k = st.columns(5)
k[0].metric("Year 5 revenue", money(y5["Revenue"]), f"from {money(y1['Revenue'])} in Year 1", delta_color="off")
k[1].metric("Year 5 operating income", money(y5["Operating income"]),
            f"{y5['Operating income'] / y5['Revenue']:.1%} margin", delta_color="off")
k[2].metric("First profitable year", m["first_profitable"] or "Not in 5 yrs",
            f"Paid back in {m['payback']}" if m["payback"] else "Not paid back by Year 5",
            delta_color="normal" if m["payback"] else "inverse")
k[3].metric("Peak cash needed", money(m["peak_cash"]), "largest cumulative loss", delta_color="off")
k[4].metric("LTV to CAC, Year 1", f"{y1['LTV to CAC']:.1f}x",
            ("Meets" if y1["LTV to CAC"] >= 3 else "Below") + f" 3.0x target · Y5 {y5['LTV to CAC']:.1f}x",
            delta_color="normal" if y1["LTV to CAC"] >= 3 else "inverse")

# ---------- Charts ----------
years = df.index.tolist()
c1, c2 = st.columns(2)

fig = go.Figure()
for col, color in [("Subscriptions", BLUE), ("Playbooks", ORANGE), ("Attorney memberships", AQUA), ("AI usage overages", YELLOW)]:
    fig.add_bar(x=years, y=df[col], name=col, marker_color=color, hovertemplate="%{y:$,.0f}")
fig.update_layout(barmode="stack")
chart(c1, fig, "Revenue by stream", f"Subscriptions make up {y5['Subscriptions'] / y5['Revenue']:.1%} of Year 5 revenue. Our report estimated about 60%.")

fig = go.Figure()
fig.add_scatter(x=years, y=df["Revenue"], name="Revenue", line=dict(color=BLUE, width=2), hovertemplate="%{y:$,.0f}")
fig.add_scatter(x=years, y=df["Total costs"], name="Total costs", line=dict(color=ORANGE, width=2), hovertemplate="%{y:$,.0f}")
chart(c2, fig, "Revenue vs. total costs", f"Fixed costs are {y5['Fixed costs'] / y5['Total costs']:.0%} of Year 5 costs, so each new customer adds far more revenue than cost.")

c3, c4 = st.columns(2)
cum = df["Cumulative operating income"]
fig = go.Figure(go.Bar(x=years, y=cum, marker_color=[BLUE if v >= 0 else RED for v in cum],
                       text=[money(v) for v in cum], textposition="outside", cliponaxis=False, hovertemplate="%{y:$,.0f}",
                       name="Running total"))
chart(c3, fig, "Cumulative operating income", f"Early losses are paid back in {m['payback']}. At the low point we would need {money(m['peak_cash'])} in cash."
           if m["payback"] else f"Losses are not paid back within 5 years. At the low point we would need {money(m['peak_cash'])} in cash.")

be = df["Break-even subscribers"].replace(float("inf"), None)
fig = go.Figure()
fig.add_scatter(x=years, y=be, name="Break-even subscribers", line=dict(color=GRAY, width=2, dash="dash"), hovertemplate="%{y:,.0f}")
fig.add_scatter(x=years, y=df["Avg subscribers"], name="Average active subscribers", line=dict(color=BLUE, width=2), hovertemplate="%{y:,.0f}")
hit = df.index[df["Avg subscribers"] >= df["Break-even subscribers"]]
chart(c4, fig, "Subscribers vs. break-even",
      f"Subscribers pass break-even in {hit[0]}." if len(hit) else "Subscribers stay below break-even through Year 5.",
      money_axis=False)

# ---------- P&L table ----------
st.subheader("Projected P&L")
money_cols = ["Revenue", "Subscriptions", "Playbooks", "Attorney memberships", "AI usage overages",
              "Variable costs", "Fixed costs", "Operating income", "Cumulative operating income",
              "CAC (fully loaded)", "Blended LTV"]
table = df[money_cols + ["Avg subscribers", "Attorneys", "LTV to CAC"]].T
st.dataframe(
    table.style.format(lambda v: f"${v:,.0f}", subset=(money_cols, years))
               .format(lambda v: f"{v:,.0f}", subset=(["Avg subscribers", "Attorneys"], years))
               .format(lambda v: f"{v:.1f}x", subset=(["LTV to CAC"], years)),
    width="stretch",
)
st.download_button("Download this scenario as CSV", df.to_csv().encode(), "busxlaw_scenario.csv", "text/csv")

st.caption("Pricing comes from the BusXLaw Final Report (Section 7). Every other input is a team assumption we plan to test "
           "in 2027. Figures are projections before taxes and leave out startup funding and one-time build costs. "
           "LTV = contribution per subscriber-month ÷ monthly churn, blended with one-time playbook buyers. "
           "CAC = marketing plus 15% of staff time, divided by new paid customers.")
