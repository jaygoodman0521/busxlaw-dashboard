"""BusXLaw 5-year pro forma and unit economics.

Same math as BusXLaw_Financial_Model.xlsx. Pricing comes from the final report;
every other input is a team assumption that has not been tested yet.
"""
from dataclasses import dataclass, field, replace

import pandas as pd


@dataclass(frozen=True)
class Assumptions:
    # Pricing (BusXLaw Final Report, Sec. 7)
    p_playbook: float = 49
    p_starter: float = 29
    p_pro: float = 79
    p_attorney: float = 100
    p_usage: float = 4          # AI overage per subscriber-month
    # Owner funnel
    demo: tuple = (10_000, 25_000, 45_000, 70_000, 100_000)
    demo_mult: float = 1.0
    conv: float = 0.05
    playbook_share: float = 0.55
    starter_share: float = 0.70
    churn: float = 0.06         # monthly
    # Attorney side
    attorneys: tuple = (15, 35, 60, 90, 120)
    att_mult: float = 1.0
    # Variable costs
    ai_sub: float = 3.00
    ai_playbook: float = 1.00
    ai_demo: float = 0.10
    pp_pct: float = 0.029
    pp_fee: float = 0.30
    support: float = 2.00
    # Fixed costs per year
    staff: tuple = (120_000, 240_000, 380_000, 520_000, 660_000)
    legal: tuple = (20_000, 30_000, 40_000, 50_000, 60_000)
    insurance: tuple = (8_000, 8_800, 9_700, 10_600, 11_700)
    software: tuple = (12_000, 18_000, 24_000, 30_000, 36_000)
    marketing: tuple = (30_000, 60_000, 90_000, 120_000, 150_000)
    acq_staff: float = 0.15     # share of staff cost spent winning customers


BASE = Assumptions()
SCENARIOS = {
    "Low": dict(demo_mult=0.6, conv=0.03, churn=0.09, att_mult=0.6),
    "Base": dict(demo_mult=1.0, conv=0.05, churn=0.06, att_mult=1.0),
    "High": dict(demo_mult=1.4, conv=0.07, churn=0.04, att_mult=1.3),
}


def scenario(name: str, **overrides) -> Assumptions:
    return replace(BASE, **{**SCENARIOS[name], **overrides})


def run_model(a: Assumptions) -> pd.DataFrame:
    rows, end, cum = [], 0.0, 0.0
    for i in range(5):
        demo = a.demo[i] * a.demo_mult
        paid = demo * a.conv
        pbb = paid * a.playbook_share
        new = paid - pbb
        start = end
        end = start * (1 - a.churn) ** 12 + new * (1 - a.churn) ** 6
        avg = (start + end) / 2
        sm = avg * 12
        att = a.attorneys[i] * a.att_mult

        r_pb = pbb * a.p_playbook
        r_st = sm * a.starter_share * a.p_starter
        r_pro = sm * (1 - a.starter_share) * a.p_pro
        r_att = att * 12 * a.p_attorney
        r_use = sm * a.p_usage
        rev = r_pb + r_st + r_pro + r_att + r_use

        v_ai = sm * a.ai_sub + pbb * a.ai_playbook + demo * a.ai_demo
        v_pp = rev * a.pp_pct + (sm + pbb + att * 12) * a.pp_fee
        v_sup = sm * a.support
        var = v_ai + v_pp + v_sup
        fix = a.staff[i] + a.legal[i] + a.insurance[i] + a.software[i] + a.marketing[i]
        oi = rev - var - fix
        cum += oi

        cac = (a.marketing[i] + a.staff[i] * a.acq_staff) / paid if paid else 0
        arpu = (r_st + r_pro + r_use) / sm if sm else 0
        cm = arpu - (a.ai_sub + a.support + arpu * a.pp_pct + a.pp_fee)
        ltv = cm / a.churn
        pbc = a.p_playbook - a.ai_playbook - a.p_playbook * a.pp_pct - a.pp_fee
        bltv = (1 - a.playbook_share) * ltv + a.playbook_share * pbc
        ac = a.p_attorney - a.p_attorney * a.pp_pct - a.pp_fee
        left = max(0, fix - (pbb * pbc + att * ac * 12 - demo * a.ai_demo))
        be = left / (cm * 12) if cm > 0 else float("inf")

        rows.append({
            "Year": f"Year {i + 1}", "Demo users": demo, "Paid customers": paid,
            "Subscribers (end)": end, "Avg subscribers": avg, "Attorneys": att,
            "Subscriptions": r_st + r_pro, "Playbooks": r_pb, "Attorney memberships": r_att,
            "AI usage overages": r_use, "Revenue": rev, "Variable costs": var,
            "Fixed costs": fix, "Total costs": var + fix, "Operating income": oi,
            "Cumulative operating income": cum, "CAC (fully loaded)": cac,
            "Blended LTV": bltv, "LTV to CAC": bltv / cac if cac else 0,
            "Break-even subscribers": be,
        })
    return pd.DataFrame(rows).set_index("Year")


def milestones(df: pd.DataFrame) -> dict:
    def first(mask):
        hits = df.index[mask]
        return hits[0] if len(hits) else None
    return {
        "first_profitable": first(df["Operating income"] > 0),
        "payback": first(df["Cumulative operating income"] > 0),
        "peak_cash": max(0.0, -df["Cumulative operating income"].min()),
    }
