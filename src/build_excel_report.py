from pathlib import Path
import json, pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.chart import BarChart, LineChart, Reference
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'data'/'processed'; REPORTS=ROOT/'reports'; DEST=ROOT/'excel'/'Sales_Performance_Summary.xlsx'
if not (OUT/'monthly_kpis.csv').exists(): raise SystemExit('Run python src/analyze_sales.py first.')
summary=json.loads((REPORTS/'summary.json').read_text())
monthly=pd.read_csv(OUT/'monthly_kpis.csv'); products=pd.read_csv(OUT/'product_performance.csv').head(20); countries=pd.read_csv(OUT/'country_performance.csv').head(20)
wb=Workbook(); ws=wb.active; ws.title='Executive Summary'
ws.append(['SALES PERFORMANCE & BUSINESS INSIGHTS']); ws.append(['Source',summary['data_source']]); ws.append(['Period',f"{summary['analysis_period_start']} to {summary['analysis_period_end']}"]); ws.append(['Metric','Value'])
for k,v in [('Total Revenue (GBP)',summary['net_sales_gbp']),('Orders',summary['unique_invoices']),('Known Customers',summary['unique_customers_known']),('Unique Products',summary['unique_products']),('Countries',summary['countries']),('Average Order Value (GBP)',summary['average_order_value_gbp']),('Valid Sales Rows',summary['valid_positive_sales_rows'])]: ws.append([k,v])
ws.append([]); ws.append(['Data note','Revenue = Quantity × UnitPrice; GBP. See README for cleaning rules.'])
for cell in ws[1]: cell.font=Font(bold=True,size=16,color='FFFFFF'); cell.fill=PatternFill('solid',fgColor='17365D')
for c in ws[4]: c.font=Font(bold=True,color='FFFFFF'); c.fill=PatternFill('solid',fgColor='1F4E78')
for row in ws.iter_rows():
 for c in row: c.alignment=Alignment(vertical='center')
ws.column_dimensions['A'].width=34; ws.column_dimensions['B'].width=70; ws.freeze_panes='A5'
def sheet(name,df):
 sh=wb.create_sheet(name); sh.append(list(df.columns))
 for row in df.itertuples(index=False,name=None): sh.append([None if pd.isna(x) else x for x in row])
 for c in sh[1]: c.font=Font(bold=True,color='FFFFFF'); c.fill=PatternFill('solid',fgColor='1F4E78')
 sh.freeze_panes='A2'; sh.auto_filter.ref=sh.dimensions
 for col in sh.columns:
  letter=col[0].column_letter; sh.column_dimensions[letter].width=min(32,max(12,max(len(str(x.value or '')) for x in col[:200])+2))
 return sh
sm=sheet('Monthly KPIs',monthly); pr=sheet('Top Products',products); co=sheet('Country Performance',countries)
chart=LineChart(); chart.title='Monthly Revenue (GBP)'; chart.y_axis.title='Revenue (£)'; chart.x_axis.title='Year-Month'; chart.height=8; chart.width=18
chart.add_data(Reference(sm,min_col=2,min_row=1,max_row=sm.max_row),titles_from_data=True); chart.set_categories(Reference(sm,min_col=1,min_row=2,max_row=sm.max_row)); sm.add_chart(chart,'G2')
bar=BarChart(); bar.type='bar'; bar.title='Top Products by Revenue'; bar.x_axis.title='Revenue (£)'; bar.y_axis.title='Product'; bar.height=9; bar.width=18
bar.add_data(Reference(pr,min_col=3,min_row=1,max_row=pr.max_row),titles_from_data=True); bar.set_categories(Reference(pr,min_col=2,min_row=2,max_row=pr.max_row)); pr.add_chart(bar,'G2')
DEST.parent.mkdir(exist_ok=True); wb.save(DEST); print(f'Created {DEST}')
