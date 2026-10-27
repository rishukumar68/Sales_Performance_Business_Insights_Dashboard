"""Descriptive sales analysis for UCI Online Retail. No machine learning."""
from pathlib import Path
import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "processed"
REPORTS = ROOT / "reports"
OUT.mkdir(parents=True, exist_ok=True); REPORTS.mkdir(parents=True, exist_ok=True)

def load_data():
    xlsx = RAW / "Online Retail.xlsx"
    csv = RAW / "sample_sales_synthetic.csv"
    if xlsx.exists():
        df = pd.read_excel(xlsx)
        source = "UCI Online Retail dataset"
    elif csv.exists():
        df = pd.read_csv(csv)
        source = "synthetic smoke-test sample (not real business data)"
    else:
        raise FileNotFoundError("Place UCI's Online Retail.xlsx in data/raw, or use included synthetic sample.")
    # Standardize source columns
    df.columns = [str(c).strip() for c in df.columns]
    ren = {'InvoiceNo':'InvoiceNo','StockCode':'StockCode','Description':'Description','Quantity':'Quantity','InvoiceDate':'InvoiceDate','UnitPrice':'UnitPrice','CustomerID':'CustomerID','Country':'Country'}
    df = df.rename(columns=ren)
    required = list(ren)
    missing = [c for c in required if c not in df.columns]
    if missing: raise ValueError(f"Dataset missing columns: {missing}")
    df['InvoiceDate'] = pd.to_datetime(df['InvoiceDate'], errors='coerce')
    for c in ['Quantity','UnitPrice','CustomerID']: df[c] = pd.to_numeric(df[c], errors='coerce')
    audit = {'source':source,'rows_loaded':len(df),'duplicate_rows':int(df.duplicated().sum()),'missing_customer_id':int(df.CustomerID.isna().sum()),'missing_description':int(df.Description.isna().sum())}
    df = df.drop_duplicates().copy()
    df = df.dropna(subset=['InvoiceNo','StockCode','InvoiceDate','Quantity','UnitPrice','Description','Country'])
    # Cancellation invoices begin with C; negative quantity/price rows are excluded from positive-sales KPIs.
    df['InvoiceNo'] = df['InvoiceNo'].astype(str)
    df['IsCancellation'] = df['InvoiceNo'].str.upper().str.startswith('C')
    df['Revenue'] = df['Quantity'] * df['UnitPrice']
    sales = df.loc[(~df['IsCancellation']) & (df['Quantity'] > 0) & (df['UnitPrice'] > 0)].copy()
    sales['InvoiceDate'] = pd.to_datetime(sales['InvoiceDate'])
    sales['YearMonth'] = sales['InvoiceDate'].dt.to_period('M').astype(str)
    sales['Year'] = sales['InvoiceDate'].dt.year
    sales['Month'] = sales['InvoiceDate'].dt.month
    sales['OrderValue'] = sales.groupby('InvoiceNo')['Revenue'].transform('sum')
    audit.update({'rows_after_dedup_and_required_fields':len(df),'valid_positive_sales_rows':len(sales),'cancellation_rows':int(df['IsCancellation'].sum()),'unique_invoices':int(sales.InvoiceNo.nunique()),'unique_products':int(sales.StockCode.nunique()),'unique_customers_known':int(sales.CustomerID.nunique()),'countries':int(sales.Country.nunique()),'sales_revenue_gbp':round(float(sales.Revenue.sum()),2)})
    return sales, audit, source

def main():
    df,audit,source=load_data()
    df.to_csv(OUT/'clean_sales.csv',index=False)
    monthly=df.groupby('YearMonth',as_index=False).agg(Revenue=('Revenue','sum'),Orders=('InvoiceNo','nunique'),Units=('Quantity','sum'),Customers=('CustomerID','nunique'))
    products=df.groupby(['StockCode','Description'],as_index=False).agg(Revenue=('Revenue','sum'),Units=('Quantity','sum'),Orders=('InvoiceNo','nunique')).sort_values('Revenue',ascending=False)
    countries=df.groupby('Country',as_index=False).agg(Revenue=('Revenue','sum'),Orders=('InvoiceNo','nunique'),Customers=('CustomerID','nunique')).sort_values('Revenue',ascending=False)
    orders=df.groupby('InvoiceNo',as_index=False).agg(OrderDate=('InvoiceDate','min'),Revenue=('Revenue','sum'),CustomerID=('CustomerID','first'),Country=('Country','first'))
    orders['YearMonth']=orders.OrderDate.dt.to_period('M').astype(str)
    monthly.to_csv(OUT/'monthly_kpis.csv',index=False); products.to_csv(OUT/'product_performance.csv',index=False); countries.to_csv(OUT/'country_performance.csv',index=False); orders.to_csv(OUT/'orders.csv',index=False)
    summary={'data_source':source,**audit,'net_sales_gbp':round(float(df.Revenue.sum()),2),'average_order_value_gbp':round(float(orders.Revenue.mean()),2),'top_product_by_revenue':str(products.iloc[0]['Description']) if len(products) else None,'top_country_by_revenue':str(countries.iloc[0]['Country']) if len(countries) else None,'analysis_period_start':str(df.InvoiceDate.min().date()),'analysis_period_end':str(df.InvoiceDate.max().date())}
    pd.Series(summary).to_json(REPORTS/'summary.json',indent=2)
    print('\nSALES ANALYSIS SUMMARY')
    for k,v in summary.items(): print(f'{k}: {v}')
    print('\nCreated data/processed/*.csv and reports/summary.json')
if __name__=='__main__': main()
