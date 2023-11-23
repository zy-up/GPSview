from GPSSerial import RTKGPSReader
from UI  import MyApp
from logtool import setup_GPS_logger

import threading
from time import sleep
from queue import Queue

import serial
import serial.tools.list_ports

def gps_thread_function(gps_reader, GPS_info_queue, Setting_queue, ser, stop_event, GPSdatalogger):

    print("准备读取GPS串口数据")
    while not stop_event.is_set():
        sleep(0.01)

        # 获取UI设置参数
        if not Setting_queue.empty():
            EPSG = Setting_queue.get_nowait()
            EPSG = "epsg:" + EPSG
            gps_reader.changeepsg(EPSG)

        # 等待串口打开
        if ser.is_open:
            try:   
                line = gps_reader.read_line()
            except:
                print("GPS串口关闭退出")
            # 打印串口原始数据
            print(line)
            data = gps_reader.parse_line(line)
            if data:
                # 打印接收的GPS解析数据
                # print(data)
                # 将度分坐标数据转变为十进制与平面坐标数据
                lat_dd, lon_dd, easting, northing = gps_reader.convert_to_plane_coordinate(
                    data['latitude'], data['latitude_direction'], data['longitude'], data['longitude_direction'])
                # 将数据压栈，使其能够在其他线程中被读取
                GPS_info_queue.put((data, lat_dd, lon_dd, easting, northing))
                # 输出平面坐标数据
                # print(f"Easting: {easting}, Northing: {northing}")

                log_message = f"Data: {data}, Latitude: {lat_dd}, Longitude: {lon_dd}, Easting: {easting}, Northing: {northing}"
                GPSdatalogger.info(log_message)



if __name__ == '__main__':
    # 压栈用于线程间的数据安全传递
    GPS_info_queue = Queue()
    Setting_queue = Queue()
    
    GPSdatalogger = setup_GPS_logger("MyAppLogger")
    GPSdatalogger.info("This is an info message.")

    # 获取串口句柄
    ser = serial.Serial()

    # 实例化界面
    app = MyApp(ser, GPS_info_queue, Setting_queue)
    stop_event = app.stop_event

    # 实例化串口读取
    gps_reader = RTKGPSReader(ser)  # 替换为你的串口 需要拿到串口句柄，坐标系，过滤器设置，误差设置
    gps_thread = threading.Thread(target=gps_thread_function, args=(gps_reader, GPS_info_queue, 
                                    Setting_queue, ser, stop_event, GPSdatalogger))
    gps_thread.start()

    # 阻塞运行界面循环
    app.run()

    gps_thread.join()
