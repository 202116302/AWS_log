import psycopg2
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import os


def get_db_connection():
    return psycopg2.connect(
        host='localhost',
        database='aws_log',
        user='hyejin',
        password='smartfarm'
    )


def get_weather_data(start_date=None, end_date=None, days=7):
    """Get weather data from PostgreSQL"""
    conn = get_db_connection()

    if start_date and end_date:
        query = """
            SELECT timestamp, temp, humid, radn
            FROM weather_data
            WHERE DATE(timestamp) BETWEEN %s AND %s
            ORDER BY timestamp
        """
        df = pd.read_sql_query(query, conn, params=(start_date, end_date))
    else:
        query = """
            SELECT timestamp, temp, humid, radn
            FROM weather_data
            WHERE timestamp >= NOW() - INTERVAL '%s days'
            ORDER BY timestamp
        """
        df = pd.read_sql_query(query, conn, params=(days,))

    conn.close()
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    return df


def get_today_data():
    """Get today's weather data only"""
    conn = get_db_connection()
    query = """
        SELECT timestamp, temp, humid, radn
        FROM weather_data
        WHERE DATE(timestamp) = CURRENT_DATE
        ORDER BY timestamp
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    return df


def create_today_graph(df, output_path='weather_today.png'):
    """Create today's weather graph with hourly detail"""
    if df.empty:
        print("❌ No data available for today")
        return

    today_str = df['timestamp'].iloc[0].strftime('%Y-%m-%d')

    fig, axes = plt.subplots(3, 1, figsize=(14, 10))
    fig.suptitle(f'Smart Farm Weather Data - {today_str}', fontsize=16, fontweight='bold')

    # Temperature
    axes[0].plot(df['timestamp'], df['temp'], color='#e74c3c', linewidth=2.5, marker='o', markersize=5,
                 label='Temperature')
    axes[0].fill_between(df['timestamp'], df['temp'], alpha=0.2, color='#e74c3c')
    axes[0].set_ylabel('Temperature (°C)', fontsize=12, fontweight='bold')
    axes[0].grid(True, alpha=0.3)
    axes[0].legend(loc='upper right')
    axes[0].set_ylim(bottom=0)

    # Add max/min annotations
    if not df['temp'].isna().all():
        max_temp_idx = df['temp'].idxmax()
        min_temp_idx = df['temp'].idxmin()
        axes[0].plot(df.loc[max_temp_idx, 'timestamp'], df.loc[max_temp_idx, 'temp'],
                     'r^', markersize=10, label=f"Max: {df.loc[max_temp_idx, 'temp']:.1f}°C")
        axes[0].plot(df.loc[min_temp_idx, 'timestamp'], df.loc[min_temp_idx, 'temp'],
                     'bv', markersize=10, label=f"Min: {df.loc[min_temp_idx, 'temp']:.1f}°C")

    # Humidity
    axes[1].plot(df['timestamp'], df['humid'], color='#3498db', linewidth=2.5, marker='o', markersize=5,
                 label='Humidity')
    axes[1].fill_between(df['timestamp'], df['humid'], alpha=0.2, color='#3498db')
    axes[1].set_ylabel('Humidity (%)', fontsize=12, fontweight='bold')
    axes[1].grid(True, alpha=0.3)
    axes[1].legend(loc='upper right')
    axes[1].set_ylim(0, 100)

    # Add average line
    if not df['humid'].isna().all():
        avg_humid = df['humid'].mean()
        axes[1].axhline(y=avg_humid, color='#3498db', linestyle='--', linewidth=2,
                        alpha=0.5, label=f'Avg: {avg_humid:.1f}%')

    # Solar Radiation
    axes[2].plot(df['timestamp'], df['radn'], color='#f39c12', linewidth=2.5, marker='o', markersize=5,
                 label='Solar Radiation')
    axes[2].fill_between(df['timestamp'], df['radn'], alpha=0.2, color='#f39c12')
    axes[2].set_ylabel('Solar Radiation (W/m²)', fontsize=12, fontweight='bold')
    axes[2].set_xlabel('Time', fontsize=12, fontweight='bold')
    axes[2].grid(True, alpha=0.3)
    axes[2].legend(loc='upper right')
    axes[2].set_ylim(bottom=0)

    # Add sunrise/sunset indication (simplified - assuming 6am-6pm)
    if not df['radn'].isna().all():
        total_radn = df['radn'].sum()
        axes[2].text(0.02, 0.95, f'Total: {total_radn:.1f} W/m²',
                     transform=axes[2].transAxes, fontsize=10,
                     verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    # Date format - show hours for today
    for ax in axes:
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        ax.xaxis.set_major_locator(mdates.HourLocator(interval=2))  # Every 2 hours
        ax.tick_params(axis='x', rotation=45)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✅ Today's graph saved: {output_path}")
    plt.close()


def create_today_combined_graph(df, output_path='weather_today_combined.png'):
    """Create today's combined graph"""
    if df.empty:
        print("❌ No data available for today")
        return

    today_str = df['timestamp'].iloc[0].strftime('%Y-%m-%d')

    fig, ax = plt.subplots(figsize=(14, 7))

    # Normalize data to 0-100 range
    temp_normalized = (df['temp'] / df['temp'].max()) * 100 if df['temp'].max() > 0 else df['temp']
    humid_normalized = df['humid']
    radn_normalized = (df['radn'] / df['radn'].max()) * 100 if df['radn'].max() > 0 else df['radn']

    ax.plot(df['timestamp'], temp_normalized, color='#e74c3c', linewidth=3, marker='o', markersize=5,
            label='Temperature (normalized)', alpha=0.8)
    ax.plot(df['timestamp'], humid_normalized, color='#3498db', linewidth=3, marker='s', markersize=5,
            label='Humidity (%)', alpha=0.8)
    ax.plot(df['timestamp'], radn_normalized, color='#f39c12', linewidth=3, marker='^', markersize=5,
            label='Solar Radiation (normalized)', alpha=0.8)

    ax.set_xlabel('Time', fontsize=12, fontweight='bold')
    ax.set_ylabel('Value (0-100)', fontsize=12, fontweight='bold')
    ax.set_title(f'Smart Farm Weather Data - {today_str}', fontsize=16, fontweight='bold')
    ax.legend(loc='upper right', fontsize=11)
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.set_ylim(0, 105)

    # Hour format
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    ax.xaxis.set_major_locator(mdates.HourLocator(interval=2))
    plt.xticks(rotation=45)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✅ Today's combined graph saved: {output_path}")
    plt.close()


def create_weather_graph(df, output_path='weather_graph.png', title='Smart Farm Weather Data'):
    """Create temperature, humidity, and solar radiation line graphs"""
    fig, axes = plt.subplots(3, 1, figsize=(12, 10))
    fig.suptitle(title, fontsize=16, fontweight='bold')

    # Temperature
    axes[0].plot(df['timestamp'], df['temp'], color='#e74c3c', linewidth=2, marker='o', markersize=3,
                 label='Temperature')
    axes[0].fill_between(df['timestamp'], df['temp'], alpha=0.2, color='#e74c3c')
    axes[0].set_ylabel('Temperature (°C)', fontsize=12, fontweight='bold')
    axes[0].grid(True, alpha=0.3)
    axes[0].legend(loc='upper right')
    axes[0].set_ylim(bottom=0)

    # Humidity
    axes[1].plot(df['timestamp'], df['humid'], color='#3498db', linewidth=2, marker='o', markersize=3, label='Humidity')
    axes[1].fill_between(df['timestamp'], df['humid'], alpha=0.2, color='#3498db')
    axes[1].set_ylabel('Humidity (%)', fontsize=12, fontweight='bold')
    axes[1].grid(True, alpha=0.3)
    axes[1].legend(loc='upper right')
    axes[1].set_ylim(0, 100)

    # Solar Radiation
    axes[2].plot(df['timestamp'], df['radn'], color='#f39c12', linewidth=2, marker='o', markersize=3,
                 label='Solar Radiation')
    axes[2].fill_between(df['timestamp'], df['radn'], alpha=0.2, color='#f39c12')
    axes[2].set_ylabel('Solar Radiation (W/m²)', fontsize=12, fontweight='bold')
    axes[2].set_xlabel('Time', fontsize=12, fontweight='bold')
    axes[2].grid(True, alpha=0.3)
    axes[2].legend(loc='upper right')
    axes[2].set_ylim(bottom=0)

    # Date format
    for ax in axes:
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
        ax.tick_params(axis='x', rotation=45)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✅ Graph saved: {output_path}")
    plt.close()


def create_combined_graph(df, output_path='weather_combined.png', title='Smart Farm Weather Data'):
    """Create combined line graph with normalized values"""
    fig, ax = plt.subplots(figsize=(14, 7))

    # Normalize data to 0-100 range
    temp_normalized = (df['temp'] / df['temp'].max()) * 100 if df['temp'].max() > 0 else df['temp']
    humid_normalized = df['humid']
    radn_normalized = (df['radn'] / df['radn'].max()) * 100 if df['radn'].max() > 0 else df['radn']

    ax.plot(df['timestamp'], temp_normalized, color='#e74c3c', linewidth=2.5, marker='o', markersize=4,
            label='Temperature (normalized)', alpha=0.8)
    ax.plot(df['timestamp'], humid_normalized, color='#3498db', linewidth=2.5, marker='s', markersize=4,
            label='Humidity (%)', alpha=0.8)
    ax.plot(df['timestamp'], radn_normalized, color='#f39c12', linewidth=2.5, marker='^', markersize=4,
            label='Solar Radiation (normalized)', alpha=0.8)

    ax.set_xlabel('Time', fontsize=12, fontweight='bold')
    ax.set_ylabel('Value (0-100)', fontsize=12, fontweight='bold')
    ax.set_title(title, fontsize=16, fontweight='bold')
    ax.legend(loc='upper right', fontsize=11)
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.set_ylim(0, 105)

    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
    plt.xticks(rotation=45)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✅ Combined graph saved: {output_path}")
    plt.close()


def create_daily_summary_graph(df, output_path='weather_daily.png', title='Daily Weather Summary'):
    """Create daily average summary as line graphs"""
    df['date'] = df['timestamp'].dt.date
    daily_df = df.groupby('date').agg({
        'temp': 'mean',
        'humid': 'mean',
        'radn': 'mean'
    }).reset_index()

    # Convert date to datetime for proper plotting
    daily_df['date'] = pd.to_datetime(daily_df['date'])

    fig, axes = plt.subplots(3, 1, figsize=(12, 10))
    fig.suptitle(title, fontsize=16, fontweight='bold')

    # Temperature
    axes[0].plot(daily_df['date'], daily_df['temp'], color='#e74c3c', linewidth=3, marker='o', markersize=8,
                 label='Avg Temperature')
    axes[0].fill_between(daily_df['date'], daily_df['temp'], alpha=0.3, color='#e74c3c')
    axes[0].set_ylabel('Temperature (°C)', fontsize=12, fontweight='bold')
    axes[0].grid(True, alpha=0.3)
    axes[0].legend()

    # Humidity
    axes[1].plot(daily_df['date'], daily_df['humid'], color='#3498db', linewidth=3, marker='o', markersize=8,
                 label='Avg Humidity')
    axes[1].fill_between(daily_df['date'], daily_df['humid'], alpha=0.3, color='#3498db')
    axes[1].set_ylabel('Humidity (%)', fontsize=12, fontweight='bold')
    axes[1].grid(True, alpha=0.3)
    axes[1].legend()
    axes[1].set_ylim(0, 100)

    # Solar Radiation
    axes[2].plot(daily_df['date'], daily_df['radn'], color='#f39c12', linewidth=3, marker='o', markersize=8,
                 label='Avg Solar Radiation')
    axes[2].fill_between(daily_df['date'], daily_df['radn'], alpha=0.3, color='#f39c12')
    axes[2].set_ylabel('Solar Radiation (W/m²)', fontsize=12, fontweight='bold')
    axes[2].set_xlabel('Date', fontsize=12, fontweight='bold')
    axes[2].grid(True, alpha=0.3)
    axes[2].legend()

    # Date format
    for ax in axes:
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
        ax.tick_params(axis='x', rotation=45)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✅ Daily summary saved: {output_path}")
    plt.close()


def main():
    output_dir = './graphs'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    print("📊 Generating weather graphs...")

    # 1. Today's data
    print("\n📅 Generating today's graphs...")
    today_df = get_today_data()
    if not today_df.empty:
        create_today_graph(today_df, output_path=f'{output_dir}/weather_today.png')
        create_today_combined_graph(today_df, output_path=f'{output_dir}/weather_today_combined.png')
    else:
        print("⚠️ No data available for today")

    # 2. Last 7 days data
    print("\n📅 Generating 7-day graphs...")
    df = get_weather_data(days=7)

    if df.empty:
        print("❌ No data available for last 7 days")
        return

    print(f"✅ Fetched {len(df)} records")
    print(f"📅 Period: {df['timestamp'].min()} ~ {df['timestamp'].max()}")

    create_weather_graph(
        df,
        output_path=f'{output_dir}/weather_separate.png',
        title='Smart Farm Weather Data (Last 7 Days)'
    )

    create_combined_graph(
        df,
        output_path=f'{output_dir}/weather_combined.png',
        title='Smart Farm Weather Data - Combined View'
    )

    create_daily_summary_graph(
        df,
        output_path=f'{output_dir}/weather_daily.png',
        title='Daily Weather Summary'
    )

    print("\n🎉 All graphs generated!")
    print(f"📂 Location: {output_dir}/")
    print("\n📊 Generated graphs:")
    print("  - weather_today.png (Today's hourly data)")
    print("  - weather_today_combined.png (Today's combined view)")
    print("  - weather_separate.png (7-day separate view)")
    print("  - weather_combined.png (7-day combined view)")
    print("  - weather_daily.png (Daily summary)")


if __name__ == '__main__':
    main()