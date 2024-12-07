import pandas as pd
import numpy as np
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
from sklearn.preprocessing import MinMaxScaler
import matplotlib.pyplot as plt


path="./data.csv"
df=pd.read_csv(path)


df['Order Date']=df['Order Date'].astype(str)
df[['Order Date','Order Time']]=df['Order Date'].str.split(' ',expand=True)
df['Order Hour']=df['Order Time'].str[:2]
df['Order DateTime']=pd.to_datetime(df['Order Date']+' '+df['Order Hour']+':00')
df.set_index('Order DateTime',inplace=True)
hourly_sales=df['Order ID'].resample('H').count()
hourly_sales=hourly_sales.fillna(0)

# Scaling data to 0-1 range for LSTM
scaler=MinMaxScaler(feature_range=(0,1))
hourly_sales_scaled=scaler.fit_transform(hourly_sales.values.reshape(-1, 1))
train_size=int(len(hourly_sales_scaled)*0.8)
train,test=hourly_sales_scaled[:train_size],hourly_sales_scaled[train_size:]

# Function to create sequences of data for LSTM
def create_sequences(data, seq_length=24):
    X, y = [], []
    for i in range(len(data) - seq_length):
        X.append(data[i:i+seq_length])
        y.append(data[i + seq_length])
    return np.array(X), np.array(y)

# Setting sequence length to 24 (24 hours of data to predict the next hour)
seq_length = 24
X_train, y_train = create_sequences(train, seq_length)
X_test, y_test = create_sequences(test, seq_length)

# Reshaping data to [samples, time steps, features] for LSTM
X_train = X_train.reshape((X_train.shape[0], X_train.shape[1], 1))
X_test = X_test.reshape((X_test.shape[0], X_test.shape[1], 1))

# Building the LSTM model
model = Sequential()
model.add(LSTM(50, activation='relu', input_shape=(X_train.shape[1], 1)))
model.add(Dense(1))
model.compile(optimizer='adam', loss='mse')

# Training the model
history = model.fit(X_train, y_train, epochs=20, batch_size=32, validation_data=(X_test, y_test), verbose=1)

# Predicting the next 120 hours (5 days)
forecast_steps = 24
predictions = []

# Use the last observed sequence as input to predict next hours
current_input = X_test[-1]

for _ in range(forecast_steps):
    pred = model.predict(current_input.reshape((1, seq_length, 1)))
    predictions.append(pred[0, 0])

    # Append the prediction to create the next input sequence
    current_input = np.append(current_input[1:], pred, axis=0)

# Inverse scaling of predictions
predictions = scaler.inverse_transform(np.array(predictions).reshape(-1, 1))

# Creating a DataFrame to store forecasted values
forecasted_dates = pd.date_range(start=hourly_sales.index[-1] + pd.Timedelta(hours=1), periods=forecast_steps, freq='h')
forecasted_sales_df = pd.DataFrame(predictions, index=forecasted_dates, columns=['Forecasted Sales'])

# Printing hourly forecast for each day
for day, group in forecasted_sales_df.groupby(forecasted_sales_df.index.date):
    print(f"Sales forecast for {day}:")
    for hour, sales in zip(group.index.hour, group['Forecasted Sales']):
        print(f"{hour}: {round(sales):.0f} sales")  # Removed [0] since sales is already a float
    print("\n" + "-" * 30 + "\n")

# Plot observed and forecasted sales
plt.figure(figsize=(12, 6))
plt.plot(hourly_sales.index[-len(test):], scaler.inverse_transform(test), label='Observed')
plt.plot(forecasted_sales_df.index, forecasted_sales_df['Forecasted Sales'], color='red', label='Forecast')
plt.title("Hourly Sales Forecast from 2nd Jan 2020 to 6th Jan 2020")
plt.xlabel("Date")
plt.ylabel("Sales")
plt.legend()
plt.show()


from sklearn.metrics import mean_absolute_error, mean_squared_error

# Getting model predictions on test data
y_pred = model.predict(X_test)

# Inverse scaling for true and predicted values on the test set
y_test_unscaled = scaler.inverse_transform(y_test.reshape(-1, 1))
y_pred_unscaled = scaler.inverse_transform(y_pred)

# Calculating error metrics
mae = mean_absolute_error(y_test_unscaled, y_pred_unscaled)
mse = mean_squared_error(y_test_unscaled, y_pred_unscaled)
rmse = np.sqrt(mse)

print(f"Mean Absolute Error (MAE): {mae:.2f}")
print(f"Mean Squared Error (MSE): {mse:.2f}")
print(f"Root Mean Squared Error (RMSE): {rmse:.2f}")

# Plotting observed vs. predicted for the test set
plt.figure(figsize=(12, 6))
plt.plot(hourly_sales.index[-len(y_test_unscaled):], y_test_unscaled, label='Observed', color='blue')
plt.plot(hourly_sales.index[-len(y_test_unscaled):], y_pred_unscaled, label='Predicted', color='orange')
plt.title("Observed vs Predicted Sales on Test Set")
plt.xlabel("Date")
plt.ylabel("Sales")
plt.legend()
plt.show()


observed_df = pd.DataFrame({
    'Date': hourly_sales.index[-len(y_test_unscaled):],
    'Observed Sales': y_test_unscaled.flatten()
})

# Create DataFrame for predicted values
predicted_df = pd.DataFrame({
    'Date': hourly_sales.index[-len(y_pred_unscaled):],
    'Predicted Sales': y_pred_unscaled.flatten()
})

# Set Date as the index for both DataFrames for better alignment in comparison
observed_df.set_index('Date', inplace=True)
predicted_df.set_index('Date', inplace=True)

# Display the first few rows to compare
print("Observed Sales:\n", observed_df.head(10))
print("\nPredicted Sales:\n", predicted_df.head(10))