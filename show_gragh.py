import requests
from datetime import date, timedelta, datetime
import pandas as pd
import seaborn as sns
import matplotlib

matplotlib.use('TkAgg')
import matplotlib.pyplot as plt


def show_graph(df1, df2, par1, par2, name):
    plt.figure(figsize=(16, 4))

    # 첫 번째 선 그리기 (파란색)
    plt.plot(df1.index, df2[f'{par1}'], marker='o', linestyle='-', color='blue', label="all_mean")

    # 두 번째 선 그리기 (빨간색)
    plt.plot(df1.index, df1[f'{par2}'], marker='x', linestyle='--', color='red', label='week_mean')

    # 그래프 제목과 레이블 설정
    plt.title(f'{par2}')
    plt.xlabel('time')
    plt.ylabel(f'{par2}')

    # 범례 추가
    plt.legend()

    # 그래프 표시
    plt.grid(True)
    plt.savefig(f'output/{name}.png')





def aws_log():
    start_date = date(2023, 9, 26)
    end_date = date.today()

    # 날짜 범위 내의 날짜를 리스트로 저장
    date_list = [start_date + timedelta(days=x) for x in range((end_date - start_date).days + 1)]

    df_list = []

    for x in date_list:
        year = x.year
        mon = f"{x.month:02d}"
        day = f"{x.day:02d}"

        url = f"http://203.239.47.148:8080/dspnet.aspx?Site=85&Dev=1&Year={year}&Mon={mon}&Day={day}"
        context = requests.get(url).text
        data_sep = context.split("\r\n")

        data_list = [x.split(',')[:-1] for x in data_sep][:-1]

        df = pd.DataFrame(data_list, columns=['시간', '온도', '습도', 'x', 'x', 'x', '일사',
                                              '풍향', 'x', 'x', 'x', 'x', 'x', '픙속(1분 평균)', '강우', '최대순간풍속', "배터리전압"])

        df['날짜'] = df['시간'].str.split(' ').str[0]
        df['시각'] = df['시간'].str.split(' ').str[1]

        df = df.drop('x', axis=1)
        df_list.append(df)

    df_all = pd.concat(df_list)

    return df_all


def main():
    thingspeak_url = "https://api.thingspeak.com/channels/1999884/feeds.json?api_key=TYCQQ3CFQME0PITO&results=168"
    contents = requests.get(thingspeak_url)
    data = contents.json()

    temp = [x['field1'] for x in data['feeds']]
    humid = [x['field2'] for x in data['feeds']]
    sunshine = [x['field3'] for x in data['feeds']]
    wind_dir = [x['field4'] for x in data['feeds']]
    wind_speed = [x['field5'] for x in data['feeds']]
    rainfall = [x['field6'] for x in data['feeds']]
    wind_speed_max = [x['field7'] for x in data['feeds']]
    v = [x['field8'] for x in data['feeds']]

    time = [x['created_at'].replace('T', ' ').replace('Z', '') for x in data['feeds']]

    date = [datetime.strptime(x, '%Y-%m-%d %H:%M:%S') + timedelta(hours=9) for x in time]

    time_list = [x.strftime('%m-%d %H:%M') for x in date]

    df_data = {'time': time_list, 'temp': temp, 'humid': humid, 'sunshine': sunshine, "wind_dir": wind_dir,
               "wind_speed": wind_speed, 'rainfall': rainfall, "wind_speed_max": wind_speed_max, "v": v}

    df = pd.DataFrame(df_data)

    aws_data = aws_log()

    aws_data = aws_data[aws_data['시간'].str.endswith("00:00")]

    columns = ['온도', '습도', '일사', '풍향', '픙속(1분 평균)', '강우', '최대순간풍속', "배터리전압"]

    aws_data[columns] = aws_data[columns].astype(float)

    aws_data = aws_data.groupby('시각')[columns].mean().round(2)

    aws_data = aws_data.drop(aws_data.index[0])


    df['date'] = df['time'].str.split(" ").str[0]
    df['time2'] = df['time'].str.split(" ").str[1]


    columns_to_convert = ['temp', 'humid', 'sunshine', 'wind_dir', 'wind_speed', 'rainfall', 'wind_speed_max', 'v']
    df[columns_to_convert] = df[columns_to_convert].astype(float)


    data_mean = df.groupby('date')[columns_to_convert].mean().round(2)



    df = df[df['time2'].str.endswith("00")]

    data_time = df.groupby('time2')[columns_to_convert].mean().round(2)
    # print(data_time)

    ######## 시간별 데이터    전체 평균 vs 일주일 평균 비교  #####

    for item1, item2 in zip(columns, columns_to_convert):
        show_graph(data_time, aws_data, item1, item2, item2)



    ###### 일주일간 일평균 데이터  #####

    # plt.plot(data_mean.index, data_mean['temp'], marker='o', linestyle='-')
    #
    # # 일주일간 일평균 온도 그래프
    # plt.title('temperature 11-30 ~ 11-06')
    # plt.xlabel('temperature')
    # plt.ylabel('date')
    #
    # plt.show()
    #
    # plt.figure(figsize=(16, 8))  # 그래프 영역 설정
    #
    # # 서브플롯 1 (2x4 그리드 중 1)
    # plt.subplot(2, 4, 1)
    # plt.plot(data_mean.index, data_mean['temp'], marker='o', color='red')
    # plt.title('temperature')
    # plt.xlabel('date')
    # plt.ylabel('temp(℃)')
    #
    # # 서브플롯 2 (2x4 그리드 중 2)
    # plt.subplot(2, 4, 2)
    # plt.plot(data_mean.index, data_mean['humid'], marker='x', linestyle='--')
    # plt.title('humidity')
    # plt.xlabel('date')
    # plt.ylabel('humid(%)')
    #
    # # 서브플롯 3 (2x4 그리드 중 3)
    # plt.subplot(2, 4, 3)
    # plt.plot(data_mean.index, data_mean['sunshine'], marker='s', linestyle='-.', color="yellow")
    # plt.title('sunshine')
    # plt.xlabel('date')
    # plt.ylabel('lux(lx)')
    #
    # # 서브플롯 4 (2x4 그리드 중 4)
    # plt.subplot(2, 4, 4)
    # plt.plot(data_mean.index, data_mean['wind_dir'], marker='^', linestyle=':', color='black')
    # plt.title('wind_dir')
    # plt.xlabel('date')
    # plt.ylabel('dir(°)')
    #
    # plt.subplot(2, 4, 5)
    # plt.plot(data_mean.index, data_mean['wind_speed'], marker='o', color='black')
    # plt.title('wind_speed')
    # plt.xlabel('date')
    # plt.ylabel('speed(m/s')
    #
    # # 서브플롯 2 (2x4 그리드 중 2)
    # plt.subplot(2, 4, 6)
    # plt.plot(data_mean.index, data_mean['rainfall'], marker='x', linestyle='--', color='navy')
    # plt.title('rainfall')
    # plt.xlabel('date')
    # plt.ylabel('rainfall(mm)')
    #
    # # 서브플롯 3 (2x4 그리드 중 3)
    # plt.subplot(2, 4, 7)
    # plt.plot(data_mean.index, data_mean['wind_speed_max'], marker='s', linestyle='-.', color='black')
    # plt.title('wind_speed_max')
    # plt.xlabel('date')
    # plt.ylabel('speed(m/s)')
    #
    # # 서브플롯 4 (2x4 그리드 중 4)
    # plt.subplot(2, 4, 8)
    # plt.plot(data_mean.index, data_mean['v'], marker='^', linestyle=':' , color='black')
    # plt.title('battery_v')
    # plt.xlabel('date')
    # plt.ylabel('v')
    #
    # # 그래프 표시
    # plt.tight_layout()  # 그래프 간격 조정
    # plt.show()


if __name__ == '__main__':
    main()
