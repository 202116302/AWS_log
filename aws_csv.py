import requests
import pandas as pd
import os
from datetime import date, timedelta


def main():
    output_dir = 'output'
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)

    if not os.path.exists('output/data_all.csv'):
        # 시작 날짜와 오늘의 날짜 가져오기

        start_date = date(2023, 9, 26)
        end_date = date.today() # 오늘까지 데이터 받을 때 사용

        # start_date = date(2023, 10, 18)
        # end_date = date(2023, 10, 24)

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

        df_all.to_csv('output/data_all.csv', encoding='utf-8-sig', index=False)

    else:
        df2 = pd.read_csv('output/data_all.csv')

        last_date = df2.tail(1)['날짜'].str.split('-')

        start_date = date(int(last_date.str[0]), int(last_date.str[1]), int(last_date.str[2]))
        end_date = date.today()

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

        df_all2 = pd.concat(df2, df_all)


        df_all2.to_csv('output/data_all.csv', encoding='utf-8-sig', index=False)







if __name__ == '__main__':
    main()
