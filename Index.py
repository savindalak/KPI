#!/usr/bin/env python
# coding: utf-8

# In[3]:


import pandas as pd
import numpy as np
import matplotlib.pyplot as plt 


df_ampla_raw = pd.read_excel ("https://github.com/savindalak/KPI/blob/main/ampla_raw_data.xlsx",engine='openpyxl')
df_powerbi_raw = pd.read_excel('https://github.com/savindalak/KPI/blob/main/powerbi_raw_data.xlsx',engine='openpyxl')

#df_working_hours = df_powerbi_raw[df_powerbi_raw['engine_status']=='On']

# clean ampla data 

df_ampla_1 = df_ampla_raw [['Start Time','End Time','Duration','Equipment Id','Classification','Comments']]
df_ampla_1 = df_ampla_1.sort_values(by=['Equipment Id','Start Time'],ascending=[True, True])
df_ampla_1 = df_ampla_1.reset_index(drop=True)
df_ampla_1['Duplication_within_6_hours']=0
print(abs(df_ampla_1['Start Time'][12099] - df_ampla_1['Start Time'][12098])/np.timedelta64(1, 'h'))
print(df_powerbi_raw.columns)

# within 6 hours duplication filter for unplanned work 
df_ampla_1 = df_ampla_1[(df_ampla_1['Classification']=='Unscheduled Downtime (UD)')]
df_ampla_1 = df_ampla_1.reset_index(drop=True)


for i in range (1,len(df_ampla_1.axes[0])):

    if (abs(df_ampla_1['Start Time'][i] - df_ampla_1['Start Time'][i-1])/np.timedelta64(1, 'h')) <6 :
        df_ampla_1['Duplication_within_6_hours'][i] = 1
           
#print(df_ampla_1.head(40))
    
#slice data set for non duplicates and unplanned work to get breakdown count

df_ampla_filtered = df_ampla_1[(df_ampla_1['Duplication_within_6_hours']==0)]
df_ampla_filtered['year'] = pd.DatetimeIndex(df_ampla_filtered['Start Time']).year
df_ampla_filtered['month'] = pd.DatetimeIndex(df_ampla_filtered['Start Time']).month

df_ampla_breakdown_counts = df_ampla_filtered.groupby(['year','month','Equipment Id']).size().reset_index(name='counts')
df_ampla_breakdown_counts['Last_four_digits'] = df_ampla_breakdown_counts['Equipment Id'].str[-4:]

#print(df_ampla_breakdown_counts.head(40))
  
#filter powerbi data to get worked hours 

df_powerbi_ready = df_powerbi_raw[df_powerbi_raw['engine_status'] == 'On']
df_powerbi_worked_hours = df_powerbi_ready.groupby(['time - Year','time - Month','equipment_name']).sum().reset_index()
df_powerbi_worked_hours['equipment_name'] = df_powerbi_worked_hours['equipment_name'].astype(str)
df_powerbi_worked_hours['Last_four_digits'] = df_powerbi_worked_hours['equipment_name'].str[-4:]
d = {'January':1, 'February':2, 'March':3, 'April':4,'May':5,'June':6,'July':7,'August':8,'September':9,'October':10,'November':11,
    'December':12}

df_powerbi_worked_hours['time - Month'] = df_powerbi_worked_hours['time - Month'].map(d)


# merge data sets &calc MTBF
df_merged = pd.merge(df_ampla_breakdown_counts, df_powerbi_worked_hours, how="left", left_on=['year','month',"Last_four_digits"],
                     right_on=['time - Year','time - Month','Last_four_digits'])
df_merged = df_merged.dropna()
df_merged["group"] = df_merged['Equipment Id'].str[0:5]

#print(df_merged.head(40))

df_mtbf = df_merged.groupby(['year','month','group']).sum().reset_index()
df_mtbf['MTBF'] = df_mtbf['Sum of hours']/df_mtbf['counts']
print(df_mtbf.dtypes)

#Graphs for Trucks 2021 june
df_merged['MTBF'] = df_merged['Sum of hours']/df_merged['counts']
df_2021 = df_merged[df_merged['year']==2021]
df_2021_june = df_2021[df_2021['month']==6]
df_trucks = df_2021_june[df_2021_june['group']=='TRUCK']
df_trucks = df_trucks.sort_values(by=['MTBF'])
average_truck_mtbf = df_mtbf.loc[(df_mtbf['year']==2021) & (df_mtbf['group']=='TRUCK')& (df_mtbf['month']==6)]
print (average_truck_mtbf.iloc[0]['MTBF'])
average_truck_mtbf = average_truck_mtbf.iloc[0]['MTBF']

plt.figure(figsize=(10, 8), dpi=80)
plt.barh(df_trucks['Equipment Id'],df_trucks['MTBF'])
plt.ylabel("TRUCKS")
plt.xlabel('MTBF(Hours)')
plt.xticks(list(plt.xticks()[0]) + [average_truck_mtbf])
plt.axvline(x=average_truck_mtbf , linestyle='--')
plt.title('MTBF of each Truck')
plt.savefig('Trucks_MTBF')
plt.show()

#Graph for truck MTBF over 2 years 

df_truck_mtbf = df_mtbf[df_mtbf['group']=='TRUCK'].reset_index(drop=True)
df_truck_mtbf['DATE'] = pd.to_datetime(df_truck_mtbf[['year', 'month']].assign(DAY=28))

fig, ax = plt.subplots(figsize=(10,8))  
ax.scatter(df_truck_mtbf['DATE'],df_truck_mtbf['MTBF'])
ax.plot(df_truck_mtbf['DATE'],df_truck_mtbf['MTBF'])
ax.set_xticks(df_truck_mtbf['DATE'])
ax.tick_params(axis='x', rotation=90)
x=df_truck_mtbf['DATE']
y=df_truck_mtbf['MTBF']
for i,j in zip(x,y):
    ax.annotate(int(j),xy=(i,j+1))
plt.ylabel("MTBF(Hours)")
plt.xlabel('Time')
ax.set_ylim(ymin=0)
plt.title('MTBF trend of Trucks')
plt.savefig('Trucks_MTBF_trend')
plt.show()

#Graph for Excavators MTBF over 2 years 
df_excav_mtbf = df_mtbf[df_mtbf['group']=='EXCAV'].reset_index(drop=True)
df_excav_mtbf['DATE'] = pd.to_datetime(df_excav_mtbf[['year', 'month']].assign(DAY=28))

fig, ax = plt.subplots(figsize=(10,8))  
ax.scatter(df_excav_mtbf['DATE'],df_excav_mtbf['MTBF'])
ax.plot(df_excav_mtbf['DATE'],df_excav_mtbf['MTBF'])
ax.set_xticks(df_excav_mtbf['DATE'])
ax.tick_params(axis='x', rotation=90)
x=df_excav_mtbf['DATE']
y=df_excav_mtbf['MTBF']
for i,j in zip(x,y):
    ax.annotate(int(j),xy=(i,j+1))
plt.ylabel("MTBF(Hours)")
plt.xlabel('Time')
ax.set_ylim(ymin=0)
plt.title('MTBF trend of Excavators')
plt.savefig('Excavators_MTBF_trend')
plt.show()

#Graph for Scrapers MTBF over 2 years 
df_scrap_mtbf = df_mtbf[df_mtbf['group']=='SCRAP'].reset_index(drop=True)
df_scrap_mtbf['DATE'] = pd.to_datetime(df_scrap_mtbf[['year', 'month']].assign(DAY=28))

fig, ax = plt.subplots(figsize=(10,8))  
x=df_scrap_mtbf['DATE']
y=df_scrap_mtbf['MTBF']
ax.scatter(x,y)
ax.plot(x,y)
ax.set_xticks(x)
ax.tick_params(axis='x', rotation=90)

for i,j in zip(x,y):
    ax.annotate(int(j),xy=(i,j+1))
plt.ylabel("MTBF(Hours)")
plt.xlabel('Time')
ax.set_ylim(ymin=0)
plt.title('MTBF trend of Scrapers')
plt.savefig('Scrapers_MTBF_trend')
plt.show()

#Graph for Loaders MTBF over 2 years 
df_loader_mtbf = df_mtbf[df_mtbf['group']=='LOADE'].reset_index(drop=True)
df_loader_mtbf['DATE'] = pd.to_datetime(df_loader_mtbf[['year', 'month']].assign(DAY=28))

fig, ax = plt.subplots(figsize=(10,8))  
x=df_loader_mtbf['DATE']
y=df_loader_mtbf['MTBF']
ax.scatter(x,y)
ax.plot(x,y)
ax.set_xticks(x)
ax.tick_params(axis='x', rotation=90)

for i,j in zip(x,y):
    ax.annotate(int(j),xy=(i,j+1))
plt.ylabel("MTBF(Hours)")
plt.xlabel('Time')
ax.set_ylim(ymin=0)
plt.title('MTBF trend of Loaders')
plt.savefig('Loaders_MTBF_trend')
plt.show()


# In[ ]:




