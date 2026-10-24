import csv

with open('data/raw/612--payment-system-indicators--new-format.csv', 'r', encoding='utf-8') as f:
    rows = list(csv.reader(f))

header = rows[0]
col_map = {col: i for i, col in enumerate(header)}

def parse_val(row, col_name):
    if col_name is None:
        return None
    idx = col_map[col_name]
    v = row[idx].strip()
    if v in ['', '-', ' -', '" -"', "'-"]:
        return None
    try:
        return float(v.replace(',', ''))
    except:
        return None

recons = [
    ('RTGS = Cust + Interbank', 'c16', 'c17', [('c18', 'c19'), ('c20', 'c21')]),
    ('CCIL G-Sec = Outright + Repo + Triparty', 'c4', 'c5', [('c6', 'c7'), ('c8', 'c9'), ('c10', 'c11')]),
    ('CCIL Total = G-Sec + Forex + Derivatives', 'c2', 'c3', [('c4', 'c5'), ('c12', 'c13'), ('c14', 'c15')]),
    ('Credit Card = PoS + Others', 'c52', 'c53', [('c54', 'c55'), ('c56', 'c57')]),
    ('Debit Card = PoS + Others', 'c58', 'c59', [('c60', 'c61'), ('c62', 'c63')]),
    ('Total Cards = Credit + Debit', 'c50', 'c51', [('c52', 'c53'), ('c58', 'c59')]),
    ('PPI Cards = PoS + Others', 'c68', 'c69', [('c70', 'c71'), ('c72', 'c73')]),
    ('PPI Total = Wallets + Cards', 'c64', 'c65', [('c66', 'c67'), ('c68', 'c69')]),
    ('Paper = CTS + Others', 'c74', 'c75', [('c76', 'c77'), ('c78', 'c79')]),
    ('Retail Transfers (Cat 2) = 2.1..2.7', 'c22', 'c23', [('c24', 'c25'), ('c26', 'c27'), ('c28', 'c29'), ('c30', 'c31'), ('c32', 'c33'), ('c34', 'c35'), ('c36', 'c37')]),
    ('Debit Direct (Cat 3) = 3.1..3.4', 'c40', 'c41', [('c42', 'c43'), ('c44', 'c45'), ('c46', 'c47'), ('c48', 'c49')]),
    ('Total Retail = Cat 2 + 3 + 4 + 5 + 6', 'c80', 'c81', [('c22', 'c23'), ('c40', 'c41'), ('c50', 'c51'), ('c64', 'c65'), ('c74', 'c75')]),
    ('Total Payments = RTGS + Retail', 'c82', 'c83', [('c16', 'c17'), ('c80', 'c81')]),
    ('Total Digital = Total Payments - Paper', 'c84', 'c85', [('c82', 'c83'), ('-c74', '-c75')]),
    ('Mobile = Intra + Inter', 'c86', 'c87', [('c88', 'c89'), ('c90', 'c91')]),
    ('Internet = Intra + Inter', 'c92', 'c93', [('c94', 'c95'), ('c96', 'c97')]),
    ('ATM Cash = Credit + Debit + PPI', 'c98', 'c99', [('c100', 'c101'), ('c102', 'c103'), ('c104', 'c105')]),
    ('PoS Cash = Debit + PPI', 'c106', 'c107', [('c108', 'c109'), ('c110', 'c111')]),
    ('MicroATM Cash = AePS', 'c112', 'c113', [('c114', 'c115')]),
    ('Infra Cards = Credit + Debit', 'c116', None, [('c118', None), ('c120', None)]),
    ('Infra PPI = Wallets + Cards', 'c122', None, [('c124', None), ('c126', None)]),
    ('Infra ATMs = Bank + WhiteLabel', 'c128', None, [('c130', None), ('c132', None)]),
]

print(f"Checking {len(recons)} reconciliation rules across 81 months...")
mismatches = []
rule_pass = {}

for name, tot_vol_col, tot_val_col, parts in recons:
    vol_fail = 0
    val_fail = 0
    vol_pass = 0
    val_pass = 0
    
    for r in range(8, 89):
        m = rows[r][col_map['c1']]
        row = rows[r]
        
        # Check volume
        tot_vol = parse_val(row, tot_vol_col)
        sum_vol = 0
        has_none_vol = False
        for p_vol_col, p_val_col in parts:
            sign = 1
            col_name = p_vol_col
            if col_name.startswith('-'):
                sign = -1
                col_name = col_name[1:]
            pv = parse_val(row, col_name)
            if pv is None:
                has_none_vol = True
            else:
                sum_vol += sign * pv
        
        if tot_vol is not None and not has_none_vol:
            diff = round(tot_vol - sum_vol, 2)
            if abs(diff) > 0.05:
                vol_fail += 1
                if vol_fail <= 2:
                    mismatches.append(f"{name} [Vol mismatch] in {m}: Tot={tot_vol}, Sum={round(sum_vol, 2)}, Diff={diff}")
            else:
                vol_pass += 1
        elif tot_vol is None and not has_none_vol:
            vol_fail += 1
            mismatches.append(f"{name} [Tot Vol is None but parts exist] in {m}: Sum={round(sum_vol, 2)}")
            
        # Check value if applicable
        if tot_val_col is not None:
            tot_val = parse_val(row, tot_val_col)
            sum_val = 0
            has_none_val = False
            for p_vol_col, p_val_col in parts:
                sign = 1
                col_name = p_val_col
                if col_name is not None:
                    if col_name.startswith('-'):
                        sign = -1
                        col_name = col_name[1:]
                    pv = parse_val(row, col_name)
                    if pv is None:
                        has_none_val = True
                    else:
                        sum_val += sign * pv
            if tot_val is not None and not has_none_val:
                diff = round(tot_val - sum_val, 2)
                if abs(diff) > 0.05:
                    val_fail += 1
                    if val_fail <= 2:
                        mismatches.append(f"{name} [Val mismatch] in {m}: Tot={tot_val}, Sum={round(sum_val, 2)}, Diff={diff}")
                else:
                    val_pass += 1
            elif tot_val is None and not has_none_val:
                val_fail += 1
                mismatches.append(f"{name} [Tot Val is None but parts exist] in {m}: Sum={round(sum_val, 2)}")
                
    rule_pass[name] = (vol_pass, vol_fail, val_pass, val_fail)

print(f"\nReconciliation Summary by Rule:")
for r_name, (v_p, v_f, vl_p, vl_f) in rule_pass.items():
    print(f"  {r_name:40s} | Vol: {v_p} pass, {v_f} fail | Val: {vl_p} pass, {vl_f} fail")

print(f"\nTotal mismatch notices: {len(mismatches)}")
for mm in mismatches:
    print(" ", mm)
