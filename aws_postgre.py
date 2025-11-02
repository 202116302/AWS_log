import psycopg2
from datetime import datetime
import pandas as pd
import requests


def get_db_connection():
    return psycopg2.connect(
        host='localhost',
        database='smartfarm',
        user='hyejin',
        password='your_password'
    )


def get_aws(year, month, day):
    api_url = f"http://203.239.47.148:8080/dspnet.aspx?Site=85&Dev=1&Year={year}&Mon={month}&Day={day}"
    response = requests.get(api_url)
    data = response.text.strip().split('\n')
    df = pd.DataFrame([line.split(',') for line in data])

    df_clean = pd.DataFrame({
        'timestamp': pd.to_datetime(df.iloc[:, 0]),
        'temp': pd.to_numeric(df.iloc[:, 1], errors='coerce'),
        'humid': pd.to_numeric(df.iloc[:, 2], errors='coerce'),
        'radn': pd.to_numeric(df.iloc[:, 6], errors='coerce'),
        'wind_degree': pd.to_numeric(df.iloc[:, 7], errors='coerce'),
        'wind': pd.to_numeric(df.iloc[:, 13], errors='coerce'),
        'rainfall': pd.to_numeric(df.iloc[:, 14], errors='coerce'),
        'battery': pd.to_numeric(df.iloc[:, 16], errors='coerce')
    })

    return df_clean


def save_to_db(data):
    conn = get_db_connection()
    cur = conn.cursor()

    saved_count = 0
    for _, row in data.iterrows():
        try:
            cur.execute("""
                INSERT INTO weather_data 
                (timestamp, temp, humid, radn, wind_degree, wind, rainfall, battery)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (timestamp) DO NOTHING
            """, (row['timestamp'], row['temp'], row['humid'], row['radn'],
                  row['wind_degree'], row['wind'], row['rainfall'], row['battery']))
            saved_count += cur.rowcount
        except Exception as e:
            print(f"에러 발생: {e}")
            continue

    conn.commit()
    cur.close()
    conn.close()
    print(f"✅ {saved_count}개 새 데이터 저장 완료")


def main():
    current_date = datetime.now()
    year = current_date.year
    month = str(current_date.month).zfill(2)
    day = str(current_date.day).zfill(2)

    print(f"📡 {year}-{month}-{day} 기상 데이터 수집 중...")
    data = get_aws(year, month, day)
    print(f"📥 {len(data)}개 데이터 수신")
    save_to_db(data)


if __name__ == '__main__':
    main()