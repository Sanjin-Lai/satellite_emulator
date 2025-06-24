from datetime import datetime
from pprint import pprint
import ephem

from satellite_emulator.position_update import const_var as cv
from satellite_emulator.position_update import global_var as gv


# import const_var as cv
# import global_var as gv

class SatelliteNode:
    def __init__(self, tle_info: tuple, node_id: int):
        self.temp_tle = tle_info
        self.satellite = ephem.readtle(tle_info[0], tle_info[1], tle_info[2])
        self.node_id = node_id

    def get_next_position(self, time_now):
        ephem_time = ephem.Date(time_now)
        self.satellite.compute(ephem_time)
        return self.satellite.sublat, self.satellite.sublong, self.satellite.elevation

    def __str__(self):
        return "[" + self.temp_tle[0] + "\n" + self.temp_tle[1] + "\n" + self.temp_tle[2] + "]"


def worker(range_start: int, range_end: int, res, send_pipe):
    # calculated satellite nums
    calculated_satellites_num = range_end - range_start + 1
    # calculate the position of the satellites
    now = datetime.utcnow()

    for i in range(range_start, range_end + 1):
        try:
            index_base = 3 * i
            res[index_base], res[index_base + 1], res[index_base + 2] = gv.satellite_nodes[i].get_next_position(now)
        except Exception as e:
            print(e)
            print("worker index: ", i)
    send_pipe.send(calculated_satellites_num)


def get_year_day(now_time: datetime) -> (int, float):
    year = now_time.year
    day = float(now_time.microsecond)
    day /= 1000
    day += now_time.second
    day /= 60
    day += now_time.minute
    day /= 60
    day += now_time.hour
    day /= 24
    day += (now_time - datetime(year, 1, 1)).days

    return year % 100, day


def str_checksum(line: str) -> int:
    sum_num = 0
    for c in line:
        if c.isdigit():
            sum_num += int(c)
        elif c == '-':
            sum_num += 1
    return sum_num % 10


def generate_tle(orbit_num: int, sats_per_orbit: int, latitude, longitude, delta, period) -> (list, dict):
    satellites = []
    position_datas = {}
    satellite_name_base = "node_"
    freq = 1 / period
    # TLE 格式的第1行，包含卫星的名称或标识符。
    # TLE 格式的第2行，包含卫星的轨道参数。
    line_1 = "1 00000U 23666A   %02d%012.8f  .00000000  00000-0 00000000 0 0000"
    line_2 = "2 00000  90.0000 %08.4f 0000011   0.0000 %8.4f %11.8f00000"
    year2, day = get_year_day(datetime.now())

    # 对每条轨道
    for i in range(orbit_num):
        start_latitude = latitude + delta * i  # latitude 纬度
        start_longitude = longitude + 180 * i / orbit_num  # longitude 经度
        # 单轨卫星
        for j in range(sats_per_orbit):
            # 位置信息表
            node_id_str = "node_" + str(len(satellites))
            position_datas[node_id_str] = {
                cv.LATITUDE_KEY: 0.0,
                cv.LONGITUDE_KEY: 0.0,
                cv.HEIGHT_KEY: 0.0
            }
            this_latitude = start_latitude + 360 * j / sats_per_orbit
            this_line_1 = line_1 % (year2, day)
            this_line_2 = line_2 % (start_longitude, this_latitude, freq)
            # [[], [], []]
            tmp_tle_info = (satellite_name_base + str(len(satellites)),
                            this_line_1 + str(str_checksum(this_line_1)),
                            this_line_2 + str(str_checksum(this_line_2)))
            tmp_sat = SatelliteNode(tmp_tle_info, len(satellites))
            satellites.append(tmp_sat)

    return satellites, position_datas


if __name__ == "__main__":
    now_time = datetime.now()
    sat1, position_datas1 = generate_tle(3, 2, 0, 0, 0.1, 0.08)
    for item in sat1:
        print(item, file=open("./sat.txt", 'a'))