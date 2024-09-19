import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from io import BytesIO

# Define a function to get data from Yahoo Finance
def get_index_data(ticker, period='5y'):
    """Fetch historical data for a given ticker."""
    data = yf.Ticker(ticker).history(period=period)
    data['Date'] = data.index
    return data

# Define a function to calculate velocity based on 240, 480, 1200-day growth rates
def calculate_velocity(data):
    """Calculate the Velocity based on growth rates over 240, 480, and 1200 days."""
    data['240d Growth'] = (data['Close'] - data['Close'].shift(240)) / data['Close'].shift(240) * 100
    data['480d Growth'] = (data['Close'] - data['Close'].shift(480)) / data['Close'].shift(480) * 100
    data['1200d Growth'] = (data['Close'] - data['Close'].shift(1200)) / data['Close'].shift(1200) * 100
    data['Velocity'] = (data['240d Growth'] * 1/3) + (data['480d Growth'] * 1/3) + (data['1200d Growth'] * 1/3)
    return data

# Function to create downloadable CSV with timezone-unaware dates
def to_excel(df):
    # Ensure the 'Date' column is timezone-unaware before writing to Excel
    df['Date'] = df['Date'].dt.tz_localize(None)
    
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, index=False, sheet_name='Sheet1')
    writer.close()  # Correct method is close, not save
    processed_data = output.getvalue()
    return processed_data

# Create the Streamlit app
st.title('📈 Real-Time Velocity-Based Trading Dashboard')

# Sidebar to select the index for analysis
index_choice = st.sidebar.selectbox(
    '📊 Choose the index for Velocity analysis',
    ['Nasdaq 100', 'Nasdaq Composite', 'S&P 500']
)

# Map index choice to Yahoo Finance ticker symbols
ticker_mapping = {
    'Nasdaq 100': '^NDX',
    'Nasdaq Composite': '^IXIC',
    'S&P 500': '^GSPC'
}

# Get the selected ticker
selected_ticker = ticker_mapping[index_choice]

# Get real-time data for the selected index
st.write(f"Fetching data for **{index_choice}**...")
index_data = get_index_data(selected_ticker)

# Calculate velocity for the selected index
velocity_data = calculate_velocity(index_data)

# Drop rows with NaN values resulting from growth rate calculations
velocity_data.dropna(inplace=True)

# Display the Velocity graph with a header
st.subheader(f"📊 {index_choice} Velocity Data")
st.line_chart(velocity_data[['Velocity']])

# Display the data as a table and allow download as Excel
st.subheader(f"📋 {index_choice} Velocity Table")
st.dataframe(velocity_data[['Date', 'Close', '240d Growth', '480d Growth', '1200d Growth', 'Velocity']])

# Provide the download button for data
st.write("Download the data as Excel:")
df_xlsx = to_excel(velocity_data[['Date', 'Close', '240d Growth', '480d Growth', '1200d Growth', 'Velocity']])
st.download_button(label="📥 Download data", data=df_xlsx, file_name=f'{index_choice}_Velocity.xlsx')

# Display how the Velocity is calculated for today's date
latest_data = velocity_data.iloc[-1]

st.subheader(f"🔢 Velocity Calculation for {latest_data['Date'].date()}")
st.write(f"**240-day Growth:** {latest_data['240d Growth']:.2f}%")
st.write(f"**480-day Growth:** {latest_data['480d Growth']:.2f}%")
st.write(f"**1200-day Growth:** {latest_data['1200d Growth']:.2f}%")
st.write(f"**Velocity = (240-day Growth * 1/3) + (480-day Growth * 1/3) + (1200-day Growth * 1/3)**")
st.write(f"Final Velocity: **{latest_data['Velocity']:.2f}%**")

# Provide detailed trading recommendations based on Velocity thresholds
def get_trading_recommendation(velocity):
    if velocity > 150:
        return "버블구간: 매수중단 + 알파매도"
    elif 100 < velocity <= 150:
        return "과속구간: 차등 소량 매수"
    elif 50 < velocity <= 100:
        return "평속구간: 정상 매수"
    elif 0 < velocity <= 50:
        return "저속구간: 차등 과량 매수"
    elif velocity <= 0:
        return "후퇴구간: +알파 매수"

# Add a visual divider line between sections
st.write("---")

# Display Current Velocity Recommendation
st.subheader("📈 Current Velocity Recommendation")
st.write(f"**Recommendation:** {get_trading_recommendation(latest_data['Velocity'])}")

# Add another visual divider line
st.write("---")

# Display detailed trading strategy explanation
st.subheader("📑 상세한 매매 전략 설명")
st.write("""
- **Velocity**: 지수의 단기, 중기, 장기 성장률의 평균
    - **과속구간**: 차등 소량 매수
    - **평속구간**: 정상 매수
    - **저속구간**: 차등 과량 매수
    - **후퇴구간**: +알파 매수
    - **버블구간**: 매수 중지 +알파 매도

- **Velocity 구간에 따른 차등 매수**
    - Velocity 50~100% (평속구간): 50% 매수, 50% 현금확보
    - Velocity 125% (과속구간): 25% 매수, 75% 현금확보
    - Velocity 15% (저속구간): 85% 매수, 15% 현금확보
    - Velocity 0% (정지): 100% 매수

- **Alpha 매수**
    - Velocity -25% (후퇴): 100% 매수 + 후퇴분 x3배 알파매수
    - 종 매수 175%

- **Alpha 매도**
    - Velocity 150% (버블): 매수중단
    - Velocity 200% (버블): 매수중단 + 150% 초과분의 2% 부분매도
    - 50%의 2%, 가지고 있는 수량의 1% 부분매도

- **Alpha 매도에 사익 재투자**
    - Velocity 0~50% 저속구간: 계좌잔고의 1% 주가 매수
    - Velocity 〈 0% 후퇴구간: 계좌잔고의 10% 주가 알파매수
""")
