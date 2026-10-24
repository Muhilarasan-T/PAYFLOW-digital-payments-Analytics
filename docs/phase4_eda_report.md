# PAYFLOW — Phase 4: Exploratory Data Analysis & Insight Discovery Report

**Project:** PAYFLOW — Digital Payments Intelligence & Trends Analysis  
**Phase:** Phase 4 — Exploratory Data Analysis & Python Modeling  
**Primary Dataset:** Reserve Bank of India (RBI) Payment System Indicators (Table 612)  
**Analysis Period:** November 2019 to July 2026 (81 consecutive months)  
**Deliverables Produced:**  
- Jupyter Notebook: [`notebooks/phase4_exploratory_data_analysis.ipynb`](file:///c:/Users/DELL/PAYFLOW/notebooks/phase4_exploratory_data_analysis.ipynb)  
- Analytical Script: [`src/phase4_eda.py`](file:///c:/Users/DELL/PAYFLOW/src/phase4_eda.py)  
- Automated Test Suite: [`tests/test_phase4_eda.py`](file:///c:/Users/DELL/PAYFLOW/tests/test_phase4_eda.py)  
- Visual Artifacts: 9 high-resolution figures in [`visuals/phase4/`](file:///c:/Users/DELL/PAYFLOW/visuals/phase4/)  
**Author:** PAYFLOW Data Analytics Team  
**Date:** October 2026  
**Status:** Completed & 100% Validated  

---

## 1. Executive Summary

Phase 4 conducts a forensic, exploratory investigation of India's payment systems from **November 2019 to July 2026**. Using the cleaned, schema-normalized datasets from Phase 2 and the star schema architecture from Phase 3, this analysis quantifies the structural transformation of Indian retail and wholesale finance.

### Core Empirical Findings at a Glance
1. **The Exponential Ascent of UPI:** Monthly UPI transaction volume scaled from **1.22 Billion transactions** ($39.7\%$ of retail payment volume) in November 2019 to **23.66 Billion transactions** ($87.0\%$ of retail volume) in July 2026. Over the same horizon, UPI transaction value surged from **₹1.89 Trillion INR** ($6.2\%$ of retail value) to **₹29.88 Trillion INR** ($30.3\%$ of retail value).
2. **Payment Rail Use-Case Polarization:** Payment instruments have stratified into distinct economic segments based on **Average Ticket Size (ATS)**:
   - **UPI:** Micro-retail and everyday merchant payments averaging **₹1,263 to ₹1,300 INR**.
   - **IMPS:** Account-to-account commercial transfers averaging **₹19,161 to ₹19,534 INR** (more than doubling from ₹8,350 as micro-transactions migrated to UPI).
   - **NEFT:** Corporate payroll, vendor settlements, and B2B invoices averaging **₹50,000 to ₹52,431 INR**.
   - **RTGS Customer:** Large-value corporate settlements averaging **₹6.12 Million INR**.
3. **Credit vs. Debit Card Spend Divergence:** In 2020, Debit card spend ($₹6.62\text{ Trillion}$) exceeded Credit card spend ($₹6.39\text{ Trillion}$). By 2025, Credit card spend exploded to **₹23.95 Trillion** ($62.0\%$ driven by online/e-commerce), while Debit card spend collapsed to **₹4.44 Trillion** ($34.7\%$ e-commerce). The Credit-to-Debit spending ratio widened from **0.97x in 2020 to 5.46x in 2026**.
4. **The Obsolescence of Paper Cheques (CTS):** Cheque Truncation System (CTS) volume dropped by more than $50\%$ (halving from $86.5\text{ Crore}$ cheques in 2020 to $44.7\text{ Crore}$ in 2026). However, the average cheque size nearly doubled from **₹74,425 INR to ₹144,834 INR**, proving that paper cheques have become an exclusively high-value commercial instrument.
5. **Acceptance Infrastructure Asymmetry:** Physical Point-of-Sale (PoS) machines expanded moderately from $4.43\text{ Million}$ to **$10.03\text{ Million}$**, whereas asset-light, low-cost static UPI QR codes exploded from zero (pre-launch) to **803 Million deployed codes**—an **80:1 QR-to-PoS ratio**.
6. **ATM Cash Withdrawal Plateau:** Cash withdrawn at traditional ATMs peaked at $₹32.89\text{ Trillion}$ in 2022 and plateaued/declined to $₹29.03\text{ Trillion}$ in 2025. As digital payment volume multiplied, the ratio of ATM cash-out to digital payments plummeted from **$2.38\%$ in 2020 to $0.78\%$ in 2026**, while the average withdrawal size rose from **₹4,707 to ₹5,507 INR**.

---

## 2. Data Coverage & Analytical Scope

The analysis operates on the normalized Phase 2 datasets:
- **`transaction_indicators.csv`**: 4,617 rows, 19 columns ($57\text{ payment rails} \times 81\text{ consecutive months}$).
- **`infrastructure_indicators.csv`**: 1,053 rows, 18 columns ($13\text{ touchpoint indicators} \times 81\text{ consecutive months}$).
- **`data_dictionary.csv`**: 145 raw column definitions and indicator taxonomies.
- **`cleaning_exceptions.csv`**: 36 forensic exception logs.

### Treatment of Partial Years
- **2019:** Contains 2 months (`Nov-2019` and `Dec-2019`). Annual sums represent a 2-month baseline, not a full year.
- **2026:** Contains 7 months (`Jan-2026` to `Jul-2026`). Direct comparisons with full 12-month calendar years are explicitly qualified, or evaluated on a 7-month run-rate / monthly average basis.

---

## 3. Methodology & Metric Definitions

### 3.1 Denominator Discipline
To prevent double-counting and mathematical distortions:
1. **Retail Payment Market Share:**
   $$\text{UPI Volume Share (\%)} = \frac{\text{UPI Volume (Lakh)}}{\text{Total Retail Payments Volume (Lakh)}} \times 100$$
   $$\text{UPI Value Share (\%)} = \frac{\text{UPI Value (₹ Cr)}}{\text{Total Retail Payments Value (₹ Cr)}} \times 100$$
   *Total Retail Payments (`TOTAL_RETAIL_PAYMENTS`)* is the official RBI Category $2+3+4+5+6$ total. Wholesale RTGS (`Cat 1`) and CCIL settlements are strictly excluded from the retail denominator.
2. **Digital Payment Penetration:**
   $$\text{Digital Volume Share (\%)} = \frac{\text{Total Digital Payments Volume}}{\text{Total Payments Volume}} \times 100$$
   Where $\text{Total Digital Payments} = \text{Total Payments} - \text{Paper-Based Instruments (CTS + Others)}$.

### 3.2 Average Ticket Size (ATS) Formula
Average ticket size is evaluated only for transaction instruments where both volume (Lakh) and value (₹ Crores) are valid:
$$\text{ATS (INR)} = \frac{\text{Value in ₹ Crores} \times 10,000,000}{\text{Volume in Lakh} \times 100,000} = \frac{\text{Value in ₹ Crores}}{\text{Volume in Lakh}} \times 100$$
*ATS is strictly disabled for infrastructure equipment counts.*

### 3.3 Growth Rates & Temporal Formulas
- **Month-over-Month (MoM) Growth:**
  $$\text{MoM Growth (\%)} = \frac{V_t - V_{t-1}}{V_{t-1}} \times 100$$
- **Year-over-Year (YoY) Growth (12-Month Lag):**
  $$\text{YoY Growth (\%)} = \frac{V_t - V_{t-12}}{V_{t-12}} \times 100$$

---

## 4. Detailed Empirical Findings

### 4.1 Finding 1: The Ascent of UPI & Retail Payments Cannibalization
In November 2019, retail payments in India were distributed across debit cards, netbanking, IMPS, and cheques, with UPI capturing $39.68\%$ of volume and only $6.17\%$ of value. By July 2026, UPI captured **$87.00\%$ of all retail payment volume** and **$30.57\%$ of retail payment value**.

```
Annual UPI Progression Summary (2019 to 2026):
  • 2019 (2M):   2.53B txns |  ₹3.92T val | Vol Share: 39.7% | Val Share:  6.2%
  • 2020 (12M): 18.88B txns | ₹33.88T val | Vol Share: 46.6% | Val Share:  8.7%
  • 2021 (12M): 38.73B txns | ₹71.58T val | Vol Share: 60.4% | Val Share: 14.5%
  • 2022 (12M): 74.04B txns |₹125.94T val | Vol Share: 71.1% | Val Share: 19.9%
  • 2023 (12M):117.61B txns |₹182.88T val | Vol Share: 78.4% | Val Share: 24.4%
  • 2024 (12M):172.21B txns |₹246.83T val | Vol Share: 82.7% | Val Share: 27.6%
  • 2025 (12M):228.28B txns |₹299.75T val | Vol Share: 85.2% | Val Share: 29.7%
  • 2026 (7M): 156.66B txns |₹202.44T val | Vol Share: 86.8% | Val Share: 30.3%
```

The difference between volume share ($86.8\%$) and value share ($30.3\%$) illustrates why volume and value metrics must be analyzed together: while UPI completely dominates everyday transactional frequency, high-value commercial transfers remain anchored on NEFT and RTGS.

### 4.2 Finding 2: Payment Rail Use-Case Polarization & Ticket Size Dynamics
Analyzing Average Ticket Size (ATS) across rails reveals that payments in India have separated into three specialized functional tiers:

```
Average Ticket Size Comparison (Nov-2019 vs. Jul-2026):
┌────────────────────┬────────────────────┬────────────────────┬──────────────┐
│ Payment Rail       │ Nov-2019 ATS (INR) │ Jul-2026 ATS (INR) │ Net Change   │
├────────────────────┼────────────────────┼────────────────────┼──────────────┤
│ UPI                │ ₹1,552.62          │ ₹1,262.93          │ -18.7%       │
│ Debit Cards Total  │ ₹1,811.00          │ ₹2,429.69          │ +34.2%       │
│ Credit Cards Total │ ₹3,418.32          │ ₹3,440.09          │ +0.6%        │
│ IMPS               │ ₹8,896.36          │ ₹19,534.13         │ +119.6%      │
│ NEFT               │ ₹79,042.16         │ ₹51,962.65         │ -34.3%       │
│ CTS Cheques        │ ₹74,425.50         │ ₹144,113.97        │ +93.6%       │
│ RTGS Customer      │ ₹5,675,532.92      │ ₹6,138,881.43      │ +8.2%        │
└────────────────────┴────────────────────┴────────────────────┴──────────────┘
```

1. **Micro-Retail Tier (sub-₹2,000):** UPI dominates small-ticket merchant purchases. Its ATS decreased from ₹1,553 to ₹1,263 as low-value peer-to-merchant QR payments penetrated daily transit, street vendors, and retail kiosks.
2. **Consumer Credit & Discretionary Tier (₹2,500 – ₹4,500):** Credit cards average ₹3,440 (with online e-commerce transactions averaging ₹4,251), reflecting discretionary shopping, travel, and utility bill payments.
3. **Mid-Tier Commercial & Account Transfers (₹15,000 – ₹25,000):** IMPS ticket size more than doubled from ₹8,896 to ₹19,534. As micro-transfers shifted to zero-cost UPI, IMPS became a preferred tool for urgent, higher-value business and peer transfers.
4. **Institutional & Bulk Settlements (₹50,000 to ₹6.1M+):** NEFT handles structured payroll and commercial settlements ($₹52,000$ ATS), while RTGS Customer handles institutional transfers ($₹6.14\text{ Million}$ ATS).

### 4.3 Finding 3: Credit vs. Debit Card Usage & E-Commerce Dominance
While debit cards outnumber credit cards in circulation by nearly $8:1$ ($1.03\text{ Billion}$ debit cards vs. $122.9\text{ Million}$ credit cards in force in July 2026), credit card spending has outpaced debit card spending:

- **Spending Volume:** In 2020, Debit card spending was $₹6.62\text{ Trillion}$, slightly ahead of Credit cards ($₹6.39\text{ Trillion}$, ratio $0.97\text{x}$). By 2025, Credit card spending reached **₹23.95 Trillion**, while Debit card spending contracted to **₹4.44 Trillion**—a **$5.39\text{x}$ multiple** for credit cards.
- **E-Commerce Shift:** Credit card transactions shifted online, with e-commerce accounting for **$62.8\%$ of total credit card spend** in 2026 (up from $55.4\%$ in 2020). Conversely, debit card in-store PoS spending declined as consumers substituted debit swipes with UPI QR codes.

### 4.4 Finding 4: The Demise of Paper Cheques (CTS)
- Cheque Truncation System (CTS) volume fell steadily from **86.49 Crore cheques in 2020** to **55.47 Crore in 2025** (and $30.63\text{ Crore}$ through July 2026).
- Digital payments now account for **$99.98\%$ of retail transaction volume** and **$98.0\%$ of transaction value**.
- Average cheque size rose from **₹74,425 in 2019 to ₹144,834 in 2026**, confirming that individual retail consumers have almost entirely abandoned paper cheques, leaving them primarily for high-value corporate, tax, real estate, and legal transactions.

### 4.5 Finding 5: Merchant Infrastructure Expansion (PoS vs. QR Codes)
- **Point-of-Sale (PoS) Machines:** Expanded from $4.43\text{ Million}$ terminals in March 2020 to **$10.03\text{ Million}$** in July 2026 ($2.26\text{x}$ growth).
- **Static UPI QR Codes:** Exploded from zero pre-launch to **$92.5\text{ Million}$** in March 2021, and reached **803 Million deployed touchpoints** by July 2026.
- **QR-to-PoS Multiplier:** Rose from **$19.6\text{x}$ in 2021 to $80.1\text{x}$ in 2026**, demonstrating how software-based QR codes overcame the hardware capex limitations of traditional card terminals.

### 4.6 Finding 6: Cash Withdrawals vs. Digital Payment Growth
- Monthly ATM cash withdrawals peaked at $₹32.89\text{ Trillion}$ in 2022 and stabilized around $₹29.03\text{ Trillion}$ in 2025.
- As digital payments expanded from $₹145.4\text{ Trillion}$ in 2020 to $₹337.9\text{ Trillion}$ in 2025, the **ratio of ATM cash-out to digital payment value declined from $2.38\%$ to $0.78\%$**.
- The average ATM cash withdrawal rose from **₹4,707 in 2020 to ₹5,507 in 2026**, indicating consumers visit ATMs less frequently but withdraw larger amounts per trip.

### 4.7 Finding 7: Seasonality Patterns & Economic Shocks
Analyzing month-over-month (MoM) volume changes across normalized baseline years (2021–2025) highlights three clear cyclical patterns:
1. **Fiscal Year-End Surge (March):** UPI volume expands by an average of **$+9.8\%$ to $+11.0\%$ MoM in March**, driven by corporate tax deadlines, annual fee renewals, and government account settlements.
2. **Festive Quarter Surge (October–November):** Spending surges in October (**$+5.4\%$ MoM volume, $+9.6\%$ MoM value**) driven by festive Diwali, Dussehra, and e-commerce sales.
3. **Calendar Day Compression (February):** February exhibits a regular drop of **$-5.4\%$ to $-6.0\%$ MoM**, reflecting the 28-day calendar effect rather than an economic slowdown.
4. **COVID-19 Lockdown Shock (April 2020):** UPI volume dropped by **$-21.4\%$ MoM** in April 2020 (falling from $1.25\text{B}$ to $0.99\text{B}$ transactions) as economic activity paused, before rebounding by **$+23.5\%$ in May 2020**.

---

## 5. Visual Artifacts Inventory

All 9 figures were generated at 300 DPI and saved in [`visuals/phase4/`](file:///c:/Users/DELL/PAYFLOW/visuals/phase4/):

| Figure | Artifact Path | Core Insight Visualized |
| :---: | :--- | :--- |
| **01** | [`visuals/phase4/01_upi_volume_value_share.png`](file:///c:/Users/DELL/PAYFLOW/visuals/phase4/01_upi_volume_value_share.png) | Two-panel time series showing UPI volume share reaching $87.0\%$ and value share reaching $30.6\%$ of all retail payments. |
| **02** | [`visuals/phase4/02_monthly_upi_trends.png`](file:///c:/Users/DELL/PAYFLOW/visuals/phase4/02_monthly_upi_trends.png) | Monthly UPI volume scaling to $23.66\text{B}$ txns and value reaching $₹29.88\text{T}$, annotating the April 2020 lockdown dip. |
| **03** | [`visuals/phase4/03_payment_rail_ats_comparison.png`](file:///c:/Users/DELL/PAYFLOW/visuals/phase4/03_payment_rail_ats_comparison.png) | Logarithmic scale chart tracking ATS polarization across RTGS ($₹6\text{M}$), NEFT ($₹52\text{k}$), Cheques ($₹144\text{k}$), IMPS ($₹19.5\text{k}$), and UPI ($₹1,263$). |
| **04** | [`visuals/phase4/04_digital_payment_composition.png`](file:///c:/Users/DELL/PAYFLOW/visuals/phase4/04_digital_payment_composition.png) | Two-panel stacked area chart illustrating absolute volume growth and percentage composition shift toward UPI. |
| **05** | [`visuals/phase4/05_credit_vs_debit_card_trends.png`](file:///c:/Users/DELL/PAYFLOW/visuals/phase4/05_credit_vs_debit_card_trends.png) | Two-panel comparative analysis of Credit vs Debit spend value and the rise of e-commerce share to $62.8\%$ for credit cards. |
| **06** | [`visuals/phase4/06_acceptance_infrastructure_growth.png`](file:///c:/Users/DELL/PAYFLOW/visuals/phase4/06_acceptance_infrastructure_growth.png) | Merchant touchpoints comparing $10\text{M}$ PoS terminals against $803\text{M}$ QR codes, showing the $80:1$ ratio curve. |
| **07** | [`visuals/phase4/07_atm_cash_vs_digital_growth.png`](file:///c:/Users/DELL/PAYFLOW/visuals/phase4/07_atm_cash_vs_digital_growth.png) | ATM cash withdrawals versus total digital value, tracking the cash-to-digital ratio drop from $2.38\%$ to $0.78\%$. |
| **08** | [`visuals/phase4/08_rail_growth_leaders_and_decliners.png`](file:///c:/Users/DELL/PAYFLOW/visuals/phase4/08_rail_growth_leaders_and_decliners.png) | Horizontal bar chart of component growth leaders (UPI $+1,427\%$) vs decliners (Debit Online $-85\%$, PoS Cash $-99.8\%$). |
| **09** | [`visuals/phase4/09_festive_and_fiscal_seasonality.png`](file:///c:/Users/DELL/PAYFLOW/visuals/phase4/09_festive_and_fiscal_seasonality.png) | Bar chart indexing average MoM growth by calendar month, highlighting March fiscal spikes and February calendar dips. |

---

## 6. Data Quality Caveats & Limitations

1. **Absence of Sub-Channel Granularity:** The dataset reports composite UPI volume and value. A breakdown between Person-to-Person (P2P) and Person-to-Merchant (P2M) transactions cannot be calculated from Table 612.
2. **Correlation vs. Causation in Cash Trends:** While digital payments expanded and ATM cash withdrawals plateaued, this descriptive correlation does not establish direct causation. Cash in Circulation (CIC) held by the public continued to grow in absolute nominal terms over this period; digital payments substituted for incremental transactional cash rather than eliminating currency.
3. **Displaced Column `c141`:** Non-zero values in `c141` for UPI QR codes between Jan-2024 and Jan-2026 were preserved in raw form but excluded from count metrics in accordance with the Phase 2 exception register.

---

## 7. Business & Strategic Implications

### For Commercial Banks & Card Issuers
- **Credit Card Monetization:** Credit cards remain an effective consumer payment monetization engine, with spending expanding to $₹23.95\text{ Trillion}$ driven by e-commerce. Issuers should focus on rewards and co-branded cards for online spending.
- **Debit Card Repositioning:** Debit cards are no longer the primary tool for retail in-store payments. Banks should reposition debit cards for ATM backup, travel/forex, and high-security online transactions.

### For Merchant Acquirers & FinTechs
- **QR Code Ubiquity:** With $803\text{ Million}$ QR codes deployed, merchant onboarding has shifted to QR and soundbox infrastructure. Capital expenditure on physical PoS terminals should be targeted at enterprise retail, dining, and luxury retail where credit card penetration is high.
- **Monetization Challenges:** With UPI ticket sizes averaging $₹1,263$, volume growth alone does not guarantee revenue under zero MDR policies. FinTechs must monetize via merchant credit, working capital loans, and SaaS software solutions.

---

## 8. Verification & Test Summary

Automated testing in [`tests/test_phase4_eda.py`](file:///c:/Users/DELL/PAYFLOW/tests/test_phase4_eda.py) confirmed:
- Data dimensions: $4,617$ transaction rows and $1,053$ infrastructure rows.
- Chronological ordering and zero calendar gaps across 81 months.
- Share percentages strictly bounded within $[0\%, 100\%]$.
- Exact mathematical match between Python calculations and Phase 3 SQL database queries.
- Complete test suite passed (**21/21 total tests passing** across Phase 2 and Phase 4).

Phase 4 is complete. The project is ready to proceed to **Phase 5: Data Visualization & Executive Reporting**.
