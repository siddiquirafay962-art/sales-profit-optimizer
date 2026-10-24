"""Sales and Profit Optimization and Mathematical Modeling — Streamlit app."""
from pathlib import Path
import io
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
from scipy.optimize import Bounds, LinearConstraint, milp

st.set_page_config(page_title="Sales & Profit Optimizer", page_icon="📊", layout="wide")
st.markdown("**Developed By: Muhammad Rafay Siddiqui**")
st.caption("Rafay siddiqui | Department of Mathematics | University of Karachi")
BASE = Path(__file__).resolve().parent
FIELDS = ['Product', 'Selling Price', 'Unit Cost', 'Sales Quantity', 'Working Time', 'Raw Material', 'Maximum Demand']
NUMERIC = FIELDS[1:]

st.markdown("""<style>
.block-container {padding-top: 1.5rem; max-width: 1450px;}
h1,h2,h3 {letter-spacing: -0.03em;}
[data-testid="stMetric"] {padding: 16px; border: 1px solid rgba(120,130,150,.19); border-radius: 14px;}
</style>""", unsafe_allow_html=True)

@st.cache_data
def original_data():
    return pd.read_csv(BASE / 'products.csv', encoding='utf-8-sig')

def normalize(df):
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    missing = [c for c in FIELDS if c not in df.columns]
    if missing:
        raise ValueError('Missing columns: ' + ', '.join(missing))
    df = df[FIELDS].dropna(how='all')
    df['Product'] = df['Product'].fillna('').astype(str).str.strip()
    df = df[df['Product'] != ''].reset_index(drop=True)
    for c in NUMERIC:
        df[c] = pd.to_numeric(df[c], errors='coerce')
    if df[NUMERIC].isna().any().any():
        raise ValueError('Please fill all numeric cells with valid numbers.')
    if (df[NUMERIC] < 0).any().any():
        raise ValueError('Prices, costs, quantities, demand and resources cannot be negative.')
    if df['Product'].duplicated().any():
        raise ValueError('Product names must be unique.')
    for c in ['Sales Quantity', 'Maximum Demand']:
        if not np.allclose(df[c], np.round(df[c])):
            raise ValueError(f'{c} must have whole-number values.')
        df[c] = df[c].astype(int)
    return df

def analyze(df):
    d = df.copy()
    d['Unit Profit'] = d['Selling Price'] - d['Unit Cost']
    d['Revenue'] = d['Selling Price'] * d['Sales Quantity']
    d['Total Cost'] = d['Unit Cost'] * d['Sales Quantity']
    d['Profit'] = d['Revenue'] - d['Total Cost']
    d['Profit Margin (%)'] = np.where(d['Revenue'] > 0, d['Profit'] / d['Revenue'] * 100, 0)
    return d

def optimize(df, budget, target, use_working_time, max_hours, use_material, max_material, exact_target):
    n = len(df)
    if not n:
        return None, 'Add products first.'
    unit_cost = df['Unit Cost'].to_numpy(dtype=float)
    unit_profit = (df['Selling Price'] - df['Unit Cost']).to_numpy(dtype=float)
    upper = df['Maximum Demand'].to_numpy(dtype=float)
    coefficients = [unit_cost]
    limits = [float(budget)]
    if use_working_time:
        coefficients.append(df['Working Time'].to_numpy(dtype=float))
        limits.append(float(max_hours))
    if use_material:
        coefficients.append(df['Raw Material'].to_numpy(dtype=float))
        limits.append(float(max_material))
    A = np.vstack(coefficients)
    constraints = [LinearConstraint(A, -np.inf, np.array(limits))]
    if exact_target:
        constraints.append(LinearConstraint(np.ones((1, n)), [float(target)], [float(target)]))
    else:
        constraints.append(LinearConstraint(np.ones((1, n)), [0], [float(target)]))
    result = milp(c=-unit_profit, integrality=np.ones(n), bounds=Bounds(np.zeros(n), upper),
                  constraints=constraints, options={'time_limit': 30, 'mip_rel_gap': 0.00001})
    if result.x is None:
        return None, ('No feasible solution found for these limits. Try a larger budget, fewer units, '
                      'or higher maximum demand.' if result.status == 2 else 'Optimizer could not find a solution within the time limit.')
    quantities = np.rint(result.x).astype(int)
    plan = df[['Product', 'Selling Price', 'Unit Cost', 'Maximum Demand']].copy()
    plan['Quantity to Produce'] = quantities
    plan['Production Cost'] = quantities * df['Unit Cost'].to_numpy()
    plan['Optimized Revenue'] = quantities * df['Selling Price'].to_numpy()
    plan['Optimized Profit'] = quantities * unit_profit
    plan['Profit Contribution (%)'] = (plan['Optimized Profit'] / plan['Optimized Profit'].sum() * 100
                                        if plan['Optimized Profit'].sum() != 0 else 0.0)
    return plan, None

st.title('📊 Sales and Profit Optimization')
st.caption('Mathematical Modeling • Data Analysis • Integer Linear Programming')

if 'products' not in st.session_state:
    st.session_state.products = original_data().copy()

with st.sidebar:
    st.header('Project Settings')
    st.info('Excel workbook se imported 49 products. Editable data is kept for this browser session. Download CSV to save changes.')
    upload = st.file_uploader('Optional: Upload revised Excel or CSV', type=['xlsx', 'csv'])
    if upload is not None:
        if st.button('Import uploaded data', use_container_width=True):
            try:
                if upload.name.lower().endswith('.csv'):
                    imported = pd.read_csv(upload)
                else:
                    imported = pd.read_excel(upload, sheet_name='Raw_Data', header=1)
                    imported = imported.rename(columns={
                        'Selling Price (Rs.)': 'Selling Price', 'Unit Cost (Rs.)': 'Unit Cost',
                        'Working Time (Hours)': 'Working Time', 'Raw Material (Units)': 'Raw Material'
                    })
                st.session_state.products = normalize(imported)
                st.success('Data imported successfully.')
            except Exception as e:
                st.error(f'Import failed: {e}')
    if st.button('Reset to original Excel data', use_container_width=True):
        st.session_state.products = original_data().copy()
        st.rerun()
    st.divider()
    st.caption('Designed for university project demonstration. All amounts in Pakistani rupees (Rs.).')

tab1, tab2, tab3, tab4 = st.tabs(['📈 Dashboard', '✏️ Edit Products', '🎯 Optimization', 'ℹ️ Model Explanation'])
try:
    data = normalize(st.session_state.products)
except ValueError as err:
    st.error(str(err))
    st.stop()
report = analyze(data)

with tab1:
    total_revenue = report['Revenue'].sum()
    total_cost = report['Total Cost'].sum()
    total_profit = report['Profit'].sum()
    k1,k2,k3,k4,k5 = st.columns(5)
    k1.metric('Products', f'{len(report):,}')
    k2.metric('Sales Quantity', f'{report["Sales Quantity"].sum():,}')
    k3.metric('Total Revenue', f'Rs. {total_revenue:,.0f}')
    k4.metric('Total Cost', f'Rs. {total_cost:,.0f}')
    k5.metric('Total Profit', f'Rs. {total_profit:,.0f}')
    st.caption(f'Overall profit margin: {(total_profit / total_revenue * 100) if total_revenue else 0:.2f}% (profit ÷ revenue × 100)')
    a,b=st.columns(2)
    with a:
        top=report.nlargest(12, 'Profit').sort_values('Profit')
        st.plotly_chart(px.bar(top, x='Profit', y='Product', orientation='h', title='Top 12 Products by Profit', color='Profit', color_continuous_scale='Blues'), use_container_width=True)
    with b:
        top=report.nlargest(12, 'Sales Quantity').sort_values('Sales Quantity')
        st.plotly_chart(px.bar(top, x='Sales Quantity', y='Product', orientation='h', title='Top 12 by Sales Quantity', color='Sales Quantity', color_continuous_scale='Teal'), use_container_width=True)
    st.subheader('Full Product Analysis')
    st.dataframe(report, use_container_width=True, hide_index=True)
    st.download_button('Download analysis CSV', report.to_csv(index=False).encode('utf-8-sig'), 'product_analysis.csv', 'text/csv')

with tab2:
    st.write('Change product prices, costs, quantities, working time, raw material or demand. Add/delete rows with the editor controls.')
    edited = st.data_editor(data, num_rows='dynamic', use_container_width=True, hide_index=True,
                            column_config={'Product': st.column_config.TextColumn('Product', required=True),
                                           'Selling Price': st.column_config.NumberColumn('Selling Price (Rs.)', min_value=0),
                                           'Unit Cost': st.column_config.NumberColumn('Unit Cost (Rs.)', min_value=0),
                                           'Sales Quantity': st.column_config.NumberColumn('Sales Quantity', min_value=0, step=1),
                                           'Maximum Demand': st.column_config.NumberColumn('Maximum Demand', min_value=0, step=1)})
    c1,c2=st.columns(2)
    with c1:
        if st.button('Apply product changes', type='primary', use_container_width=True):
            try:
                st.session_state.products = normalize(edited)
                st.success('Changes applied. Dashboard and optimizer will use updated data.')
                st.rerun()
            except ValueError as e:
                st.error(str(e))
    with c2:
        st.download_button('Download edited product CSV', edited.to_csv(index=False).encode('utf-8-sig'),
                           'my_products.csv', 'text/csv', use_container_width=True)

with tab3:
    st.write('Maximize total profit while respecting available budget, maximum demand and production target. Quantities are whole numbers.')
    s1,s2=st.columns(2)
    with s1:
        budget=st.number_input('Available budget (Rs.)', min_value=0.0, value=100000.0, step=10000.0)
    with s2:
        target=st.number_input('Production units target', min_value=0, value=1000, step=50)
    exact=st.checkbox('Produce exactly the target units', value=True)
    st.caption('When unchecked, the optimizer may produce fewer units to maximize profit.')
    with st.expander('Optional resource limits (advanced)'):
        hours_on=st.checkbox('Limit total working hours', value=False)
        hours=st.number_input('Maximum working hours', min_value=0.0, value=10000.0)
        material_on=st.checkbox('Limit raw material units', value=False)
        material=st.number_input('Maximum raw material units', min_value=0.0, value=10000.0)
    if st.button('🚀 Run Profit Optimization', type='primary', use_container_width=True):
        plan,error=optimize(data, budget, target, hours_on, hours, material_on, material, exact)
        st.session_state.optimization = {'plan':plan, 'error':error,
             'settings':{'budget':budget,'target':target,'exact':exact,'hours_on':hours_on,
                         'hours':hours,'material_on':material_on,'material':material}}
    state=st.session_state.get('optimization')
    if state:
        if state['error']:
            st.warning(state['error'])
        else:
            plan=state['plan'];settings=state['settings']
            if len(plan) != len(data) or not np.array_equal(plan['Product'].to_numpy(), data['Product'].to_numpy()):
                st.warning('Product list changed since the last optimization. Run optimization again.')
            else:
                q=plan['Quantity to Produce'].to_numpy()
                c1,c2,c3,c4=st.columns(4)
                cost=float(plan['Production Cost'].sum()); revenue=float(plan['Optimized Revenue'].sum());profit=float(plan['Optimized Profit'].sum())
                c1.metric('Optimized Profit', f'Rs. {profit:,.0f}')
                c2.metric('Budget Used', f'Rs. {cost:,.0f}')
                c3.metric('Production Units', f'{q.sum():,}')
                c4.metric('Selected Products', f'{(q>0).sum():,}')
                st.caption(f'Remaining budget: Rs. {settings["budget"]-cost:,.0f}  •  Optimized revenue: Rs. {revenue:,.0f}  •  Optimized profit margin: {(profit/revenue*100) if revenue else 0:.2f}%')
                shown=plan[plan['Quantity to Produce']>0].sort_values('Optimized Profit', ascending=False)
                st.subheader('Recommended Production Plan')
                st.dataframe(shown, use_container_width=True, hide_index=True)
                if not shown.empty:
                    st.plotly_chart(px.bar(shown, x='Product', y='Optimized Profit', title='Optimized Profit by Selected Product'), use_container_width=True)
                st.download_button('Download complete optimization CSV', plan.to_csv(index=False).encode('utf-8-sig'),
                                   'optimized_production_plan.csv', 'text/csv')
                st.success('Verified: integer quantities, production limit, budget and product demand are enforced by the optimization model.')

with tab4:
    st.subheader('Mathematical Model')
    st.latex(r'\max Z = \sum_{i=1}^{n} (P_i-C_i)x_i')
    st.markdown('**Decision variable:** $x_i$ = whole-number quantity to produce of product $i$.  **$P_i$:** selling price per unit. **$C_i$:** cost per unit.')
    st.latex(r'\sum_{i=1}^{n} C_i x_i \leq B \quad \text{(Budget constraint)}')
    st.latex(r'0 \leq x_i \leq D_i, \quad x_i\in\mathbb{Z} \quad \text{(Demand and integer constraints)}')
    st.latex(r'\sum_{i=1}^{n} x_i = T\quad\text{(Exact target, if selected)}')
    st.write('Optional limits: total working time and raw material consumption are also constrained if enabled.')
    st.info('Revenue = price × quantity; total cost = unit cost × quantity; profit = revenue − cost. Overall profit margin = profit ÷ revenue × 100.')
    st.warning('The original workbook’s summary ranges are not completely consistent. This app recalculates directly from all imported products rather than copying the older summary totals. Results use a new optimization run, not the old Excel Solver answer report.')
st.divider()
st.caption("© 2026 | Developed by Mohammad Rafay Siddiqui")
st.divider()
st.subheader("Business Insights")

st.info(
    "This application analyzes product sales, costs, "
    "revenue and profit to support business decisions."
)

st.markdown("### Business Performance Indicators")
st.write("Revenue = Selling Price × Sales Quantity")
st.write("Profit = Revenue − Total Cost")
st.write("Profit Margin = (Profit / Revenue) × 100")
