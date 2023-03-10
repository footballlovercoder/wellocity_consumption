import altair as alt
from datetime import date
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import datetime
import regex as re
import requests
import math
from dateutil.relativedelta import relativedelta
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from smtplib import SMTP
import smtplib
import sys


url1="https://github.com/soham1993/wellocity_consumption/raw/main/wello_sale.csv"
url2="https://raw.githubusercontent.com/soham1993/wellocity_consumption/main/stock_report.csv"
@st.experimental_memo
def load_data():
        
        df = pd.read_csv(url1,sep = ',',header=0)
        stock=pd.read_csv(url2,sep = ',',header=0)
        return df,stock

if url1 is not None and url2 is not None:    
    df,stock = load_data()
    ### aggregation code
    df=df.fillna('CUSTOMER')
    df1=df[['Item Name','Qty']]
    df2=df1.groupby(by='Item Name').sum().reset_index()
    df10=df[['Item Name','Patient Name']]
    df11=df10.groupby('Item Name')['Patient Name'].nunique().reset_index()
    df11=df11.rename(columns={'Patient Name':'Unique_customers'})
    df3=df[['Item Name','Date']]
    df3['Date']=pd.to_datetime(df3['Date'])
    df4=df3.groupby(by='Item Name').max().reset_index()
    df4=df4.rename(columns={'Date':'Latest_transaction'})
    df9=df3.groupby(by='Item Name').min().reset_index() 
    df9=df9.rename(columns={'Date':'First_transaction'})
    df4=df4.merge(df9,on='Item Name')
    df4=df4.merge(df11,on='Item Name')
    final=df4.merge(df2,on='Item Name')
    m={1:'Jan',2:'Feb',3:'March',4:'Apr',5:'May',6:'Jun',7:'Jul',8:'Aug',9:'Sep',10:'Oct',11:'Nov',12:'Dec'}
    df['Date']=pd.to_datetime(pd.to_datetime(df['Date']).dt.strftime('%m/%d/%Y'))
    df['month_name']=df['Date'].apply(lambda x:m[x.month])
    df['year']=df['Date'].dt.year
    df['month_year']=df['month_name']+'_'+df['year'].astype(str)
    df5=df.pivot_table(values='Qty',index=['Item Name'],columns=['month_year'],aggfunc=np.sum).reset_index()
    df5=df5.fillna(0)
    final=final.merge(df5,on='Item Name')
    final1=final.drop(['Item Name','Latest_transaction','First_transaction','Qty','Unique_customers'],axis=1)
    cols=final1.columns.to_list()
    opt={}
    for c in cols:
        opt[c]=datetime.datetime.strptime(c, '%b_%Y').strftime('%Y-%m-01')
    opt_sort=sorted(opt.items(),key=lambda x:x[1])
    m_new=[x[0] for x in opt_sort]
    final=final[['Item Name','First_transaction','Latest_transaction','Unique_customers']+m_new]
    
    def get_qty(x):
        x=x.rstrip('.')
        res=re.split('(\d+)', x)
        if len(res)==1:
            return 1
        res1=x.split(' ')
        if 'ML' in res or 'GM' in res or 'G' in res or 'PCS ' in res or 'PCS' in res or 'PCS' in res1 or 'CREAM' in res1 or 'JELLY' in res1 or 'OINT' in res1 or 'WASH' in res1 or 'OIL' in res1 or 'CREAM(S)' in res1 or 'OINTMENT' in res1 or 'LOTION' in res1 or 'SYP' in res1 or 'SYRUP' in res1 or 'RESPULES' in res1 or 'INHALER' in res1 or 'TRANSHALER' in res1 or 'INH' in res1 or 'TRANSHEALER' in res1 or ' TRANSCAP' in res1 or 'ROTACAPS' in res1 or 'GEL' in res1 or 'TUBE' in res1 or 'POWDER' in res1:
            return 1
       
        if '*' in res:
            pos=res.index('*')
            if pos+1==len(res):
                return 0
            return max(res[pos-1],res[pos+1])
        else:
            return res[-2]
    final['qty_per_strip']=final['Item Name'].apply(lambda x:get_qty(x))
    stock=stock[['Product Name','Stock','Manufacturer Name']]
    stock['Product Name']=stock['Product Name'].apply(lambda x:x.replace("^","'"))
    final=final.rename(columns={'Item Name':'Item'})
    stock=stock.rename(columns={'Product Name':'Item'})
    final=final.merge(stock,on='Item',how='left')
    def new_qty_strips(df):
        if df['strips']<1:
            if df['strips']>0:
                return 1
            else:
                return df['qty_per_strip']
        else:
            return df['qty_per_strip']
        
    final['Stock']=final['Stock'].fillna(0)
    final['Manufacturer Name']=final['Manufacturer Name'].fillna("zzz")
    final['strips']=final['Stock'].astype(int)/final['qty_per_strip'].astype(int)
    final['qty_per_strip_new']=final.apply(lambda x:new_qty_strips(x),axis=1)
    final=final.drop(['strips'],axis=1)
    final['Strip_left']=final['Stock'].astype(int)/final['qty_per_strip_new'].astype(int)
    for col in m_new:
        final[col]=final[col].astype(int)/final['qty_per_strip_new'].astype(int)
    final=final.drop(['qty_per_strip_new'],axis=1)
    
    st.markdown("""
            <style>
                   .block-container {
                        padding-top: 2rem;
                        padding-bottom: 0rem;
                        padding-left: 5rem;
                        padding-right: 5rem;
                    }
            </style>
            """, unsafe_allow_html=True)
    
    st.header(' Consumption Data')
    st.text("")
    st.text("")
    st.text("")
    
    data=final.copy()
    data=data.rename(columns={'Item':'Item_Name'})
    
    choice=st.selectbox('Medicine Name',data['Item_Name'].values)
    data_filtered=data[data['Item_Name']==choice]
    st.markdown(
    """
<style>
[data-testid="stMetricValue"] {
    font-size: 25px;
}
</style>
""",
    unsafe_allow_html=True,
)
    st.metric('Manufacturer',data_filtered['Manufacturer Name'].values[0])
    with st.container():
        col1, col2,col3 = st.columns(3)
        with col1:
            ft=m[(pd.to_datetime(data_filtered['First_transaction'].values[0]).month)]+'-'+str(pd.to_datetime(data_filtered['First_transaction'].values[0]).year)
            st.metric('First Transaction',ft)
        with col2:
            lt=m[(pd.to_datetime(data_filtered['Latest_transaction'].values[0]).month)]+'-'+str(pd.to_datetime(data_filtered['Latest_transaction'].values[0]).year)
            st.metric('Latest Transaction',lt)
        with col3:
            st.metric('Number of unique customers',int(data_filtered['Unique_customers'].values[0]))
    
    
    st.metric('Stock Left',math.ceil(float(data_filtered['Strip_left'].values[0])))
    
          
    
    data_filtered=data_filtered.drop(['Item_Name','First_transaction','Latest_transaction','Unique_customers','Strip_left','qty_per_strip','Stock','Manufacturer Name'],axis=1)
    cols=data_filtered.columns.to_list()
    strip=[]
    st.text("")
    st.text("")
    choice=st.number_input('Choose the number of months consumption you want to check',min_value=1,max_value=12,step=1)
    cols1=cols[-int(choice):]
    column=[]
       
    for col in list(reversed(cols1)):
            strip.append(math.ceil(float(data_filtered[col].values[0])))
            column.append(datetime.datetime.strptime(col, '%b_%Y').strftime('%Y-%m')) 
   
    option = st.radio('',('Strips Sold','Sale Pattern','Net Strips Sold'))
    
    st.text(' ')
    s=0    
    if option=='Strips Sold':
       
           for col in list(reversed(cols1)):
               st.metric(label=col, value=math.ceil(float(data_filtered[col].values[0])))
      
                    
    elif option=='Sale Pattern': 
       source = pd.DataFrame(list(reversed(strip)),columns=['strips'])
       source['month']=list(reversed(column))
       source=source[['month','strips']]
       chart=alt.Chart(source).mark_bar().encode(x='month',y='strips')
       st.altair_chart(chart,use_container_width=True) 
    else:
       
            for col in list(reversed(cols1)):
                s=s+math.ceil(float(data_filtered[col].values[0]))
            st.metric('Total Strips Sold in %s months'%choice,s)
        
             
                   
      
              
    
    
    st.markdown(
    """
    <style>
    [data-testid="stSidebar"][aria-expanded="true"] > div:first-child {
        width: 420px;
    }
    [data-testid="stSidebar"][aria-expanded="false"] > div:first-child {
        width: 500px;
        margin-left: -500px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)
    def header(url):
       st.sidebar.markdown(f'<p style=color:#ff0000;font-size:24px;border-radius:2%;">{url}</p>', unsafe_allow_html=True)
    
    @st.experimental_memo
    def convert_df(df):
        # IMPORTANT: Cache the conversion to prevent computation on every rerun
        return df.to_csv().encode('utf-8')
    def send_email(send_to, subject, df):
        send_from = "duttasoham31@gmail.com"
        password = "gtpicwfujeqxlqqx"
        message = """\
        <p><strong>This Contains low stock data&nbsp;</strong></p>
        <p><br></p>
        <p><strong>Greetings&nbsp;</strong><br><strong>Wellocity&nbsp;    </strong></p>
        """
        for receiver in send_to:
                multipart = MIMEMultipart()
                multipart["From"] = send_from
                multipart["To"] = receiver
                multipart["Subject"] = subject  
                attachment = MIMEApplication(df.to_csv())
                fname='low_stock_data'
                attachment["Content-Disposition"] = 'attachment; filename=" {}"'.format(f"{fname}.csv")
                multipart.attach(attachment)
                multipart.attach(MIMEText(message, "html"))
                server = smtplib.SMTP("smtp.gmail.com", 587)
                server.starttls()
                server.login(multipart["From"], password)
                server.sendmail(multipart["From"], multipart["To"], multipart.as_string())
                server.quit()
       
    
    
    header('Low Stock Alert')
    st.text('')
    data_f=data.copy()
    data_f=data_f[['Item_Name','Manufacturer Name','First_transaction','Latest_transaction','Unique_customers','Strip_left']]
    limit=date.today()+relativedelta(months=-2)
    limit=limit.strftime('%Y-%m-01')
    data_f1=data_f[data_f['Latest_transaction']>=limit]
    data_f1=data_f1[data_f1['Strip_left']==0]
    
    data_f2=data_f[data_f['Latest_transaction']<limit]
    data_f2=data_f2[data_f2['Strip_left']==0]
    data_f2=data_f2[data_f2['Unique_customers']>10]
    
    data_f3=data_f[data_f['Latest_transaction']>=limit]
    data_f3=data_f3[data_f3['Unique_customers']>10]
    data_f3=data_f3[data_f3['Strip_left']<=3]
    res=pd.concat([data_f1,data_f2])
    res=pd.concat([res,data_f3])
    res=res.sort_values(by=['Unique_customers'],ascending=False)
    res=res[['Item_Name','Strip_left']]
    
    option = st.sidebar.radio('',('Download','Send Email'),horizontal=True)
    if option=='Download':
        csv1 = convert_df(res) 
        st.sidebar.download_button(
            label="Download low stock data",
            data=csv1,
            file_name='low_stock_data.csv',
            mime='text/csv',
        )   
    else:
        try:
            mailid = st.sidebar.text_input('Enter your Email id')
            if st.sidebar.button('Send'):
                send_email([mailid],'Low stock alert',res)
                st.sidebar.write("Mail Sent Succesfully")
        except:
            st.sidebar.write("Wrong Mail id")
   
    st.sidebar.title('Filter Data ')
          
    st.sidebar.text('')
      
    minimum=st.sidebar.number_input("Minimum Customer",min_value=1,value=1,step=1)
     
    maximum=st.sidebar.number_input("Maximum Customer",min_value=1,value=10000,step=1)
            
    if maximum<minimum:
        st.sidebar.write('Maximum cannot be less than Minimum')
    else:
        data['Unique_customers']=data['Unique_customers'].astype(int)
        data_filtered=data[(data['Unique_customers']>=minimum) & (data['Unique_customers']<=maximum) ]
    st.sidebar.text('')
    data_filtered['Latest_transaction']=pd.to_datetime(data_filtered['Latest_transaction'])
    data_filtered['Latest_transaction_new']=data_filtered['Latest_transaction'].apply(lambda x:x.strftime('%Y-%m-01'))
    mon=cols+['All Months']
    options = st.sidebar.multiselect('TimeRange (Recent transaction)',mon,'All Months')
    try:
        if options[0]!='All Months':
            opt=[]
            for c in options:
                opt.append(datetime.datetime.strptime(c,'%b_%Y').strftime('%Y-%m-01'))
            
            data_filtered=data_filtered[data_filtered['Latest_transaction_new'].isin(opt)]
    except IndexError:
        st.write('')
    
    st.sidebar.text('')
    with st.sidebar.container():
        col1, col2 = st.sidebar.columns(2)
        with col1:
            minimum1=st.sidebar.number_input("Minimum Stock",min_value=0,value=0,step=1)
            
            
        with col2:
            maximum1=st.sidebar.number_input("Maximum Stock",min_value=0,value=10000,step=1)
            
    if maximum<minimum:
        st.sidebar.write('Maximum cannot be less than Minimum')
    else:
        data_filtered['Strip_left']=data_filtered['Strip_left'].astype(int)
        data_filtered=data_filtered[(data_filtered['Strip_left']>=minimum1) & (data_filtered['Strip_left']<=maximum1) ]
    
    manuf=list(set(data_filtered['Manufacturer Name'].to_list()))+['All Manufacturers']
    manuf_options = st.sidebar.multiselect('Manufacturer', manuf,'All Manufacturers' )
    try:
        if manuf_options[0] !='All Manufacturers':
            data_filtered=data_filtered[data_filtered['Manufacturer Name'].isin(manuf_options)]
            
       
            
    except IndexError:
        st.write('')
    data_filtered=data_filtered[['Item_Name','Manufacturer Name','First_transaction','Latest_transaction','Unique_customers','Strip_left']]

   
    csv = convert_df(data_filtered) 
    st.sidebar.download_button(
        label="Download Filtered Data",
        data=csv,
        file_name='FIltered_data.csv',
        mime='text/csv',
    )    
    
else:
    st.markdown("""
            <style>
                   .block-container {
                        padding-top: 15rem;
                        padding-bottom: 0rem;
                        padding-left: 5rem;
                        padding-right: 5rem;
                    }
            </style>
            """, unsafe_allow_html=True)
    st.header('     ')
            
    
    
    
    
    
