import streamlit as st
import numpy as np
import pandas as pd
import requests
import time
import datetime
from astropy.time import Time
import os
#from main_ba import *
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

# try:

#     # if chosen == "Predictions":
#     if add_selectbox == "Predictions":
#         chosen2 = st.sidebar.radio(
#             'Which prediction?',
#             ('xpol','ypol','dX','dY','UT1-UTC')
#         )
#         st.header('Short-term prediction for 10 days:')
#         if chosen2 == 'xpol':
#             st.write('Predictions using different models for **XPOL [as]** during the epoch [MJD]:')
#             c2 = st.radio("Data visualization:",("Table","Interactive plot"), horizontal = True)
#             if c2 == "Table":
#                 st.dataframe(xp_pred, hide_index = True)
#             if c2 == "Interactive plot":
#                 st.plotly_chart(fig_xp, use_container_width=False)
                
#             col1, col2 = st.columns([1,1])
#             with col1:
#                 st.download_button(label =':arrow_heading_down: Save data as .txt :arrow_heading_down:', file_name = 'xp_preds.txt', data = texto_xp)
#             with col2:
#                 st.download_button(label =':arrow_heading_down: Save historic data as .txt :arrow_heading_down:', file_name = 'xp_historic.txt', data = texto_xp2)
#         if chosen2 == 'ypol':
#             st.write('Predictions using different models for **YPOL [as]** during the epoch [MJD]:')
#             c2 = st.radio("Data visualization:",("Table","Interactive plot"), horizontal = True)
#             if c2 == "Table":
#                 st.dataframe(yp_pred, hide_index = True)
#             if c2 == "Interactive plot":
#                 st.plotly_chart(fig_yp, use_container_width=False)

#             col1, col2 = st.columns([1,1])
#             with col1:
#                  st.download_button(label =':arrow_heading_down: Save data as .txt :arrow_heading_down:', file_name = 'yp_preds.txt', data = texto_yp)
#             with col2:
#                  st.download_button(label =':arrow_heading_down: Save historic data as .txt :arrow_heading_down:', file_name = 'yp_historic.txt', data = texto_yp2)
            
#         if chosen2 == 'dX':
#             st.write('Predictions using different models for **dX [as]** during the epoch [MJD]:')
#             c2 = st.radio("Data visualization:",("Table","Interactive plot"), horizontal = True)
#             if c2 == "Table":
#                 st.dataframe(dx_pred, hide_index = True)
#             if c2 == "Interactive plot":
#                 st.plotly_chart(fig_dx, use_container_width=False)

#             col1, col2 = st.columns([1,1])
#             with col1: 
#                  st.download_button(label =':arrow_heading_down: Save data as .txt :arrow_heading_down:', file_name = 'dx_preds.txt', data = texto_dx)
#             with col2:
#                  st.download_button(label =':arrow_heading_down: Save historic data as .txt :arrow_heading_down:', file_name = 'dx_historic.txt', data = texto_dx2)
            
#         if chosen2 == 'dY':
#             st.write('Predictions using different models for **dY [as]** during the epoch [MJD]:')
#             c2 = st.radio("Data visualization:",("Table","Interactive plot"), horizontal = True)
#             if c2 == "Table":
#                 st.dataframe(dy_pred, hide_index = True)
#             if c2 == "Interactive plot":
#                 st.plotly_chart(fig_dy, use_container_width=False)

#             col1, col2 = st.columns([1,1])
#             with col1: 
#                  st.download_button(label =':arrow_heading_down: Save data as .txt :arrow_heading_down:', file_name = 'dy_preds.txt', data = texto_dy)
#             with col2:
#                  st.download_button(label =':arrow_heading_down: Save historic data as .txt :arrow_heading_down:', file_name = 'dy_historic.txt', data = texto_dy2)
            
#         # if chosen2 == 'LOD':
#         #     st.write('Predictions using different models for ***LOD [ms]*** during the epoch [MJD]:')
#         #     c2 = st.radio("Data visualization:",("Table","Interactive plot"), horizontal = True)
#         #     if c2 == "Table":
#         #         st.dataframe(lod_pred, hide_index = True)
#         #     if c2 == "Interactive plot":
#         #         st.plotly_chart(fig_lod, use_container_width=False)
#         #     col1, col2 = st.columns([1,1])
#         #     with col1:
#         #         st.download_button(label =':arrow_heading_down: Save data as .txt :arrow_heading_down:', file_name = 'lod_preds.txt', data = texto_lod)
#         #     with col2:
#         #         st.download_button(label =':arrow_heading_down: Save historic data as .txt :arrow_heading_down:', file_name = 'lod_historic.txt', data = texto_lod2)
            
#         if chosen2 == 'UT1-UTC':
#             st.write('Predictions using different models for **UT1-UTC [s]** during the epoch [MJD]:')
#             c2 = st.radio("Data visualization:",("Table","Interactive plot"), horizontal = True)
#             if c2 == "Table":
#                 st.dataframe(dut1_pred, hide_index = True)
#             if c2 == "Interactive plot":
#                 st.plotly_chart(fig_dut1, use_container_width=False)
#             col1, col2 = st.columns([1,1])
#             with col1:
#                 st.download_button(label =':arrow_heading_down: Save data as .txt :arrow_heading_down:', file_name = 'dut1_preds.txt', data = texto_dut1)
#             with col2:
#                 st.download_button(label =':arrow_heading_down: Save historic data as .txt :arrow_heading_down:', file_name = 'dut1_historic.txt', data = texto_dut12)
        
                                                   
#     if add_selectbox == "Past predictions":
#         chosen3 = st.sidebar.radio(
#             'Which prediction?',
#             ('xpol','ypol','dX','dY','LOD','UT1-UTC')
#         )
#         add_selectbox2 = st.sidebar.radio('Using model:',('Day 1', 'Day 10'), horizontal = True, help = 'Each day is predicted 1 or 10 days ahead the last data available at that moment')
#         if add_selectbox2 == 'Day 1':
#             col1, col2, col3 = st.columns(3)
#             if chosen3 == "xpol":
#                 st.plotly_chart(fig_xp2, use_container_width=True)
#                 st.plotly_chart(fig_xp3, use_container_width=True)
#                 with col1:
#                     st.download_button(label =':arrow_heading_down: Save historic data as .txt :arrow_heading_down:', file_name = 'xp_historic.txt', data = texto_xp2)
#                 with col2:
#                     st.link_button(label = "Link to IERS EOP 14 C04 series",url = "https://datacenter.iers.org/data/latestVersion/EOP_14_C04_IAU2000A_one_file_1962-now.txt")
#                 with col3:
#                     st.link_button(label = "Link to ESMGFZ repository: AAM",url = "http://rz-vm115.gfz-potsdam.de:8080/repository/entry/show?entryid=57600abc-2c31-481e-9675-48f488b9304d")
                        
#             if chosen3 == "ypol":
#                 st.plotly_chart(fig_yp2, use_container_width=True)
#                 st.plotly_chart(fig_yp3, use_container_width=True)
#                 with col1:
#                     st.download_button(label =':arrow_heading_down: Save historic data as .txt :arrow_heading_down:', file_name = 'yp_historic.txt', data = texto_yp2)
#                 with col2:
#                     st.link_button(label = "Link to IERS EOP 14 C04 series",url = "https://datacenter.iers.org/data/latestVersion/EOP_14_C04_IAU2000A_one_file_1962-now.txt")
#                 with col3:
#                     st.link_button(label = "Link to ESMGFZ repository: AAM",url = "http://rz-vm115.gfz-potsdam.de:8080/repository/entry/show?entryid=57600abc-2c31-481e-9675-48f488b9304d")
#             if chosen3 == "dX":
#                 st.plotly_chart(fig_dx2, use_container_width=True)
#                 st.plotly_chart(fig_dx3, use_container_width=True)
#                 with col1:
#                     st.download_button(label =':arrow_heading_down: Save historic data as .txt :arrow_heading_down:', file_name = 'dx_historic.txt', data = texto_dx2)
#                 with col2:
#                     st.link_button(label = "Link to IERS EOP 14 C04 series",url = "https://datacenter.iers.org/data/latestVersion/EOP_14_C04_IAU2000A_one_file_1962-now.txt")
#             if chosen3 == "dY":
#                 st.plotly_chart(fig_dy2, use_container_width=True)
#                 st.plotly_chart(fig_dy3, use_container_width=True)
#                 with col1:
#                     st.download_button(label =':arrow_heading_down: Save historic data as .txt :arrow_heading_down:', file_name = 'dy_historic.txt', data = texto_dy2)
#                 with col2:
#                     st.link_button(label = "Link to IERS EOP 14 C04 series",url = "https://datacenter.iers.org/data/latestVersion/EOP_14_C04_IAU2000A_one_file_1962-now.txt")
#             if chosen3 == "LOD":
#                 st.plotly_chart(fig_lod2, use_container_width=True)
#                 st.plotly_chart(fig_lod3, use_container_width=True)
#                 with col1:
#                     st.download_button(label =':arrow_heading_down: Save historic data as .txt :arrow_heading_down:', file_name = 'lod_historic.txt', data = texto_lod2)
#                 with col2:
#                     st.link_button(label = "Link to IERS EOP 14 C04 series",url = "https://datacenter.iers.org/data/latestVersion/EOP_14_C04_IAU2000A_one_file_1962-now.txt")
#                 with col3:
#                     st.link_button(label = "Link to ESMGFZ repository: AAM",url = "http://rz-vm115.gfz-potsdam.de:8080/repository/entry/show?entryid=57600abc-2c31-481e-9675-48f488b9304d")
#             if chosen3 == "UT1-UTC":
#                 st.plotly_chart(fig_dut12, use_container_width=True)
#                 st.plotly_chart(fig_dut13, use_container_width=True)
#                 with col1:
#                     st.download_button(label =':arrow_heading_down: Save historic data as .txt :arrow_heading_down:', file_name = 'dut1_historic.txt', data = texto_dut12)
#                 with col2:
#                     st.link_button(label = "Link to IERS EOP 14 C04 series",url = "https://datacenter.iers.org/data/latestVersion/EOP_14_C04_IAU2000A_one_file_1962-now.txt")
#                 with col3:
#                     st.link_button(label = "Link to ESMGFZ repository: AAM",url = "http://rz-vm115.gfz-potsdam.de:8080/repository/entry/show?entryid=57600abc-2c31-481e-9675-48f488b9304d")
#         if add_selectbox2 == 'Day 10':
#             col1, col2, col3 = st.columns(3)
#             if chosen3 == "xpol":
#                 st.plotly_chart(fig_xp5, use_container_width=True)
#                 st.plotly_chart(fig_xp6, use_container_width=True)
#                 with col1:
#                     st.download_button(label =':arrow_heading_down: Save historic data as .txt :arrow_heading_down:', file_name = 'xp_historic.txt', data = texto_xp2)
#                 with col2:
#                     st.link_button(label = "Link to IERS EOP 14 C04 series",url = "https://datacenter.iers.org/data/latestVersion/EOP_14_C04_IAU2000A_one_file_1962-now.txt")
#                 with col3:
#                     st.link_button(label = "Link to ESMGFZ repository: AAM",url = "http://rz-vm115.gfz-potsdam.de:8080/repository/entry/show?entryid=57600abc-2c31-481e-9675-48f488b9304d")
                        
#             if chosen3 == "ypol":
#                 st.plotly_chart(fig_yp5, use_container_width=True)
#                 st.plotly_chart(fig_yp6, use_container_width=True)
#                 with col1:
#                     st.download_button(label =':arrow_heading_down: Save historic data as .txt :arrow_heading_down:', file_name = 'yp_historic.txt', data = texto_yp2)
#                 with col2:
#                     st.link_button(label = "Link to IERS EOP 14 C04 series",url = "https://datacenter.iers.org/data/latestVersion/EOP_14_C04_IAU2000A_one_file_1962-now.txt")
#                 with col3:
#                     st.link_button(label = "Link to ESMGFZ repository: AAM",url = "http://rz-vm115.gfz-potsdam.de:8080/repository/entry/show?entryid=57600abc-2c31-481e-9675-48f488b9304d")
#             if chosen3 == "dX":
#                 st.plotly_chart(fig_dx5, use_container_width=True)
#                 st.plotly_chart(fig_dx6, use_container_width=True)
#                 with col1:
#                     st.download_button(label =':arrow_heading_down: Save historic data as .txt :arrow_heading_down:', file_name = 'dx_historic.txt', data = texto_dx2)
#                 with col2:
#                     st.link_button(label = "Link to IERS EOP 14 C04 series",url = "https://datacenter.iers.org/data/latestVersion/EOP_14_C04_IAU2000A_one_file_1962-now.txt")
#             if chosen3 == "dY":
#                 st.plotly_chart(fig_dy5, use_container_width=True)
#                 st.plotly_chart(fig_dy6, use_container_width=True)
#                 with col1:
#                     st.download_button(label =':arrow_heading_down: Save historic data as .txt :arrow_heading_down:', file_name = 'dy_historic.txt', data = texto_dy2)
#                 with col2:
#                     st.link_button(label = "Link to IERS EOP 14 C04 series",url = "https://datacenter.iers.org/data/latestVersion/EOP_14_C04_IAU2000A_one_file_1962-now.txt")
#             if chosen3 == "LOD":
#                 st.plotly_chart(fig_lod5, use_container_width=True)
#                 st.plotly_chart(fig_lod6, use_container_width=True)
#                 with col1:
#                     st.download_button(label =':arrow_heading_down: Save historic data as .txt :arrow_heading_down:', file_name = 'lod_historic.txt', data = texto_lod2)
#                 with col2:
#                     st.link_button(label = "Link to IERS EOP 14 C04 series",url = "https://datacenter.iers.org/data/latestVersion/EOP_14_C04_IAU2000A_one_file_1962-now.txt")
#                 with col3:
#                     st.link_button(label = "Link to ESMGFZ repository: AAM",url = "http://rz-vm115.gfz-potsdam.de:8080/repository/entry/show?entryid=57600abc-2c31-481e-9675-48f488b9304d")
#             if chosen3 == "UT1-UTC":
#                 st.plotly_chart(fig_dut15, use_container_width=True)
#                 st.plotly_chart(fig_dut16, use_container_width=True)
#                 with col1:
#                     st.download_button(label =':arrow_heading_down: Save historic data as .txt :arrow_heading_down:', file_name = 'dut1_historic.txt', data = texto_dut12)
#                 with col2:
#                     st.link_button(label = "Link to IERS EOP 14 C04 series",url = "https://datacenter.iers.org/data/latestVersion/EOP_14_C04_IAU2000A_one_file_1962-now.txt")
#                 with col3:
#                     st.link_button(label = "Link to ESMGFZ repository: AAM",url = "http://rz-vm115.gfz-potsdam.de:8080/repository/entry/show?entryid=57600abc-2c31-481e-9675-48f488b9304d")
                                                         
                                                                 
#     if add_selectbox == "Prueba":
#         files = act_df(texto_xp,texto_yp,texto_dx,texto_dy,texto_dut1)
#         m = list(files.index)
#         ans1 = st.selectbox("fecha:",(m))
#         ans2 = st.radio('Elige eop', ("XPOL","YPOL","dX","dY","dUT1"),horizontal = True)
#         datos = files.at[ans1,ans2]
#         st.download_button(label = f'Download {ans2} data',data = datos, file_name = f'{ans2}_{ans1}.txt')

         
d = datetime.datetime.now()
d = d.replace(microsecond=0)
 
st.write(f'Last updated: {d} UTC')
    
#except:
#    with st.spinner(text="Data is currently being updated. This process might take a few minutes..."):
#        time.sleep(15)
#        st.rerun()

    
     


