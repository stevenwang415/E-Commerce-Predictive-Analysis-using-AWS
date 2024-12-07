#packages
import pandas as pd
from statsmodels.tsa.statespace.sarimax import SARIMAX
import matplotlib.pyplot as plt
from sklearn.metrics import mean_absolute_error, mean_squared_error
import numpy as np
import warnings
warnings.filterwarnings("ignore")

#importing data
path="./data.csv"
df=pd.read_csv(path)
df.head()


df['Order Date']=df['Order Date'].astype(str)
df[['Order Date','Order Time']]=df['Order Date'].str.split(' ',expand=True)
df['Order Hour']=df['Order Time'].str[:2]
#order_counts_per_hour=df.groupby(['Order Date','Order Hour']).size()
#print(order_counts_per_hour.loc['01-01-2019'])

#grouping date and hour for prediction
df['Order DateTime']=pd.to_datetime(df['Order Date']+' '+df['Order Hour']+':00')
df.set_index('Order DateTime',inplace=True)
hourly_sales=df['Order ID'].resample('H').count()
hourly_sales=hourly_sales.fillna(0)

p, d, q = 1, 1, 1
P, D, Q, s = 1, 1, 1, 24
sarima_model=SARIMAX(hourly_sales,order=(p,d,q),seasonal_order=(P,D,Q,s),enforce_stationarity=False,enforce_invertibility=False)
sarima_results=sarima_model.fit(disp=False)

#prediction
forecast_steps=120 #24 hours=1 day
forecast=sarima_results.get_forecast(steps=forecast_steps)
forecast_ci=forecast.conf_int()
forecasted_sales=forecast.predicted_mean
forecasted_sales_df=forecasted_sales.to_frame(name='Forecasted Sales')
forecasted_sales_df.index =pd.to_datetime(forecasted_sales_df.index)
for day, group in forecasted_sales_df.groupby(forecasted_sales_df.index.date):
    print(f"sales for {day}:")
    for hour, sales in zip(group.index.hour,group['Forecasted Sales']):
        print(f"{hour}:{round(sales):.0f} sales")
    print("\n"+"-"*30+"\n")

#plotting prediction
plt.figure(figsize=(12,6))
plt.plot(hourly_sales.index,hourly_sales,label='Observed')
plt.plot(forecast.predicted_mean.index,forecast.predicted_mean,color='red',label='Forecast')
plt.fill_between(forecast_ci.index,forecast_ci.iloc[:, 0],forecast_ci.iloc[:, 1],color='pink',alpha=0.3)
plt.title("hourly sales from 2nd jan 2020 to 6th jan 2020")
plt.xlabel("date")
plt.ylabel("sales")
plt.legend()
plt.show()


#metrics
actual_data = hourly_sales[-forecast_steps:]
predicted_data = forecasted_sales[-forecast_steps:]
mae = mean_absolute_error(actual_data, predicted_data)
mse = mean_squared_error(actual_data, predicted_data)
rmse = np.sqrt(mse)
print(f"Mean Absolute Error (MAE): {mae:.2f}")
print(f"Mean Squared Error (MSE): {mse:.2f}")
print(f"Root Mean Squared Error (RMSE): {rmse:.2f}")