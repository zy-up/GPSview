from GPSSerial import *
from viewGPS import *
from UI  import *

import threading
from time import sleep
from queue import Queue 


def gps_thread_function(gps_reader, position_queue, ser, stop_event):
    try:
        while not stop_event.is_set():
            sleep(0.01)
            if ser:
                line = gps_reader.read_line()
                print(line)
                data = gps_reader.parse_line(line)
                if data:
                    print(data)

                    lat_dd, lon_dd, easting, northing = gps_reader.convert_to_plane_coordinate(
                        data['latitude'], data['latitude_direction'], 
                        data['longitude'], data['longitude_direction'])
                    position_queue.put((data, lat_dd, lon_dd, easting, northing))
                    print(f"Easting: {easting}, Northing: {northing}")

    finally:
        return 0


if __name__ == '__main__':
    position_queue = Queue()

    ser = None

    app = MyApp(ser, position_queue)
    stop_event = app.stop_event

    gps_reader = RTKGPSReader(ser)  # 替换为你的串口 需要拿到串口句柄，坐标系，过滤器设置，误差设置

    gps_thread = threading.Thread(target=gps_thread_function, args=(gps_reader, position_queue,ser, stop_event))
    gps_thread.start()

    app.run()

    gps_thread.join()