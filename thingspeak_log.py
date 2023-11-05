from datetime import datetime
import time
import urllib.request
from urllib.error import URLError
import requests
import os

def main():
    x = datetime.now()

    year = x.year
    mon = f"{x.month:02d}"
    day = f"{x.day:02d}"

    url = f"http://203.239.47.148:8080/dspnet.aspx?Site=85&Dev=1&Year={year}&Mon={mon}&Day={day}"
    context = requests.get(url).text
    data_sep = context.split("\r\n")

    data_list = [x.split(',')[:-1] for x in data_sep][:-1]

    last_data = data_list[-1]

    del last_data[3:6]
    del last_data[8:13]

    thingspeak_key = os.environ['THINGSPEAK_KEY']

    urllib.request.urlopen(
        "https://api.thingspeak.com/update?api_key={}&field1={:0.1f}&field2={:0.1f}&field3={:0.1f}&field4={:0.1f}&field5={:0.1f}&field6={:0.1f}&field7={:0.1f}&field8={:0.1f}".format(thingspeak_key,
            float(last_data[1]), float(last_data[2]), float(last_data[3]), float(last_data[4]), float(last_data[5]),
            float(last_data[6]), float(last_data[7]), float(last_data[8])))


#
if __name__ == '__main__':
    main()
