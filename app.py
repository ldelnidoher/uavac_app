import streamlit as st
import numpy as np
import pandas as pdquests
import time
import datetime
from astropy.time import Time
import os
import matplotlib.pyplot as plt
import altair as alt
import plotly.graph_objects as go
import sqlite3


text1 = 'The prediction of the parameters is calculated using **Machine Learning** algorithms. The prediction horizon extends 10 days into the future, in addition to the day on which the calculations are conducted, referred to as Day 0.'
text2 = '[IERS EOP 20 C04](https://datacenter.iers.org/data/latestVersion/EOP_20_C04_IAU2000A_one_file_1962-now.txt) and [GFZ Effective Angular Momentum Functions](http://rz-vm115.gfz-potsdam.de:8080/repository/entry/show?entryid=e0fff81f-dcae-469e-8e0a-eb10caf2975b) are employed as input data.'
text3 = 'Two predictive models are applied. **w/o EAM** utilises only EOP data as input whereas **w/ EAM** includes both EOP data and Effective Angular Momentum data.'

st.set_page_config(layout = 'wide', page_title='EOP prediction', page_icon = ':earth_africa:')

custom_html = """
<div class="banner">
     <img src="https://github.com/ldelnidoher/stream_app/blob/main/logos.png?raw=true" alt="Banner Image">
</div>
<style>
     <center>
         .banner {
             width: 100%;
             height: 70px;
             overflow: hidden;
         }
         .banner img {
             width: 75%;
             object-fit: cover;
         }
    </center>
</style>
"""
st.components.v1.html(custom_html)

#add_selectbox = st.sidebar.radio('Choose data to show:',
#("Predictions", "Past predictions", "Models","Prueba","Contact info"))
add_selectbox = st.sidebar.radio('Choose data to show:',
                                 ('EOP predictions','Contact info'))
if add_selectbox == "Contact info":
    st.markdown('UAVAC: [link](https://web.ua.es/en/uavac/)')
    st.markdown('IGN Geodesy: [link](https://www.ign.es/web/ign/portal/gds-area-geodesia)')
    st.markdown('RAEGE: [link](https://raege.eu/)')
if add_selectbox == "EOP predictions":
    try:
        db_path = 'db.db' 
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("""SELECT * from polls_files """)
        dff=pd.read_sql("""SELECT * from polls_files """, conn)
        conn.close()
    
        dates = dff['pub_date'].values
        year = [s[:4] for s in dates]
        month = [m[5:7] for m in dates]
        day = [d[8:10] for d in dates]
        
        dff.insert(0, column = 'year', value = year)
        dff.insert(1, column = 'month', value = month)
        dff.insert(2, column = 'day', value = day)
         
        
        st.title('Short-term EOP predictions: 10 days')
        st.write(text1)
        st.markdown(text2) 
        st.divider() 
        selected = st.selectbox('Choose an EOP:', ('xpol', 'ypol', 'dX', 'dY', 'UT1-UTC'),) 
        eop = ['xpol', 'ypol', 'dX', 'dY', 'UT1-UTC']
        if selected == 'xpol':
             val = 'xp'
        if selected == 'ypol':
             val = 'yp'
        if selected == 'dX':
             val = 'dx'
        if selected == 'dY':
             val = 'dy'
        if selected == 'UT1-UTC':
             val = 'dt' 
        st.subheader(f'Predictions for {selected:}')
        st.write(text3) 
    
         
        df2 = dff[dff['param']==val]
        df_mjd = dff[dff['param'] == 'mj']
        st.write('Filters:') 
        col1,col2,col3 = st.columns(3)
        with col1:
             years = st.selectbox(label = '1.- Select a year:', options = list(set(df2.year.values)))
             df3 = df2[df2['year']==years]
        with col2:
             months = st.selectbox(label = '2.- Select a month:', options = list(set(df3.month.values)))
             df4 = df3[df3['month']==months]
        with col3:
             days = st.selectbox(label = '3.- Select a day:', options = list(set(df4.day.values)))
             df5 = df4[df4['day']==days]
    
        conv1 = (df5[df5['type_EAM'] == 0])["values"].iloc[0]
        conv2 = (df5[df5['type_EAM'] == 1])["values"].iloc[0]
        conv_dates = ((df5[df5['type_EAM'] == 0])["pub_date"].values)[0]
        epochs = (df_mjd[df_mjd["pub_date"] == conv_dates])["values"].iloc[0]
        epochs = [int(float(item)) for item in epochs.split(',')] 
        conv1 =  [float(item) for item in conv1.split(',')] 
        conv2 =  [float(item) for item in conv2.split(',')]  
        dates_fmt = [(Time(item,format = 'mjd').to_value('datetime')).strftime("%Y-%m-%d %H:%M:%S") for item in epochs]
        if val in 'dt':
             txt = 's'
             fm = '% .9f'
        if val in {'dx','dy'}:
             txt = 'mas'
             fm = '% 5f'
        else:
             txt = 'as'
             fm = '% .8f'
         
        df = pd.DataFrame({'Date':dates_fmt,'Epoch [MJD]':epochs, f'w/o EAM [{txt}]':conv1, f'w/ EAM [{txt}]':conv2}, index = (['Day'+str(v) for v in range(11)]))
        styles = [dict(selector="", props=[('border','2px solid #fb9a5a')]), dict(selector="th", props=[("background-color","#b2d6fb"),('color','black')])] 
        s = df.style.set_table_styles(styles)
        st.table(s)
         
        np.savetxt('param.txt',df, fmt = ['% s','%5d',f'{fm}',f'{fm}'], delimiter=' \t', header = 'Date | Epoch [MJD] | w/o EAM | w/EAM')
        f = open('param.txt','r') 
        lista =f.read()
        f.close()
         
        if selected == 'UT1-UTC':
             string = 'dut1'
        else:
             string = selected
             
        col1,col2 = st.columns([0.2,0.8],gap = 'small')
        with col1:
             st.download_button(label =':arrow_heading_down: Save data as .txt :arrow_heading_down:', file_name = f'{string}_{epochs[0]}.txt', data = lista)
        with col2:
             st.download_button(label =':arrow_heading_down: Save data as .csv :arrow_heading_down:', file_name = f'{string}_{epochs[0]}.csv', data = df.to_csv(index = False))
         
         
        fig = go.Figure()
        for j in range(1,3):
             fig.add_trace(go.Scatter(
                 x = df['Epoch [MJD]'],y = df[df.columns[-j]],
                 mode = 'lines+markers', marker = dict(size = 5), line = dict(width = 1.5),name = df.columns[-j]))
        fig.add_shape(type="rect", xref="paper", yref="paper",x0=-0.07, y0=-0.25, x1=1.13, y1=1.1, line=dict(color="#fb9a5a",width=2))
        fig.update_layout(legend_title_text = "Models")
        fig.update_xaxes(title_text="MJD")
        fig.update_yaxes(title_text=f"{txt}")
        
        st.plotly_chart(fig, use_container_width=True)
         
        st.divider() 
    
    except:
        with st.spinner(text="Uploading. This process might take a few minutes..."):
            time.sleep(15)
            st.rerun()

d = datetime.datetime.now()
d = d.replace(microsecond=0)
 
st.write(f'Last updated: {d} UTC')
    
     


