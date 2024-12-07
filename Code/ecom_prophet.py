from prophet import Prophet
import pandas as pd
import matplotlib.pyplot as plt

# Load and preprocess data
path = "./data1.csv"
df = pd.read_csv(path)

header_row = df.columns
df_cleaned = df[~df.apply(lambda row: row.astype(str).str.contains('|'.join(header_row)).any(), axis=1)]
df_cleaned = df_cleaned.dropna(how='all')  # Removes rows where all columns are NaN
df_cleaned = df_cleaned[~df_cleaned.apply(lambda row: row.str.strip().eq('').all(), axis=1)]  # Removes rows with just empty strings
df_cleaned.reset_index(drop=True, inplace=True)
df=df_cleaned

# Convert the 'Order Date' column to datetime with error handling
df['Order Date'] = pd.to_datetime(df['Order Date'], format='%m/%d/%y %H:%M')
df['Order Date'] = df['Order Date'].dt.strftime('%d-%m-%Y %H:%M')
# Convert order date and time to datetime format and set up for Prophet
df['Order Date'] = df['Order Date'].astype(str)
df[['Order Date', 'Order Time']] = df['Order Date'].str.split(' ', expand=True)
df['Order Hour'] = df['Order Time'].str[:2]
df['Order DateTime'] = pd.to_datetime(df['Order Date'] + ' ' + df['Order Hour'] + ':00')

print(df.iloc[0])
# Aggregate data by hour for Prophet
hourly_sales = df.groupby('Order DateTime').size().reset_index(name='y')
hourly_sales.rename(columns={'Order DateTime': 'ds'}, inplace=True)

# Split data into training and test sets
train_size = int(len(hourly_sales) * 0.8)
train_data = hourly_sales.iloc[:train_size]
test_data = hourly_sales.iloc[train_size:]



# Initialize Prophet model and fit to the data
model = Prophet()
model.fit(hourly_sales)

# Define the forecast period (120 hours or 5 days)
future = model.make_future_dataframe(periods=24, freq='H')

forecast = model.predict(future)
forecast_test = forecast[['ds', 'yhat']].set_index('ds').loc[test_data['ds']]

# Generate forecast
forecast = model.predict(future)

# Print hourly forecasted sales per day for the forecasted period
forecast['yhat'] = forecast['yhat'].round()
forecasted_sales_df = forecast[['ds', 'yhat']]
forecasted_sales_df.set_index('ds', inplace=True)

for day, group in forecasted_sales_df['yhat'].groupby(forecasted_sales_df.index.date):
    print(f"Sales forecast for {day}:")
    for hour, sales in zip(group.index.hour, group):
        print(f"{hour}: {int(sales)} sales")
    print("\n" + "-" * 30 + "\n")

# Plot the forecast
fig = model.plot(forecast)
plt.title("Hourly Sales Forecast from 2nd Jan 2020 to 6th Jan 2020")
plt.xlabel("Date")
plt.ylabel("Sales")
plt.show()

import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error
# Calculate error metrics
mae = mean_absolute_error(test_data['y'], forecast_test['yhat'])
mse = mean_squared_error(test_data['y'], forecast_test['yhat'])
rmse = np.sqrt(mse)

print(f"Mean Absolute Error (MAE): {mae:.2f}")
print(f"Mean Squared Error (MSE): {mse:.2f}")
print(f"Root Mean Squared Error (RMSE): {rmse:.2f}")
