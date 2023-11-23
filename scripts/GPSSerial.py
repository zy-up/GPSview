import serial
import re
from pyproj import Transformer
 
class RTKGPSReader:
    def __init__(self, ser):
        epsg_code = "epsg:5186"
        self.ser = ser
        self.transformer = Transformer.from_crs("epsg:4326", epsg_code, always_xy=True)

    def open_port(self, port, baudrate):
        """打开串口连接"""
        self.ser = serial.Serial(port, baudrate)

    def read_line(self):
        """读取串口中的一行数据"""
        if self.ser and self.ser.is_open:
            return self.ser.readline().decode('utf-8').strip()
        else:
            return None

    def parse_line(self, line):
        """解析NMEA句子"""
        if line.startswith('$GNGGA'):
            # 这里可以根据需要解析更多字段
            parts = line.split(',')
            if  parts[7]!='00':
                return {
                    'time': parts[1],
                    'latitude': parts[2],
                    'latitude_direction': parts[3],
                    'longitude': parts[4],
                    'longitude_direction': parts[5],
                    'fix_quality': parts[6],
                    'num_satellites': parts[7],
                    'horizontal_dilution': parts[8],
                    'altitude': parts[9],
                    'altitude_units': parts[10],
                    'geoidal_separation': parts[11],
                    'geoidal_units': parts[12],
                    'age_of_diff_corr': parts[13],
                }
            return None
        return None

    @staticmethod
    def dms_to_dd(dms, direction):
        """将度分格式转换为十进制度"""
        split_dms = re.split(r'(\d+)(\d{2}\.\d+)', dms)
        split_dms = list(filter(None, split_dms))
        degrees = float(split_dms[0])
        minutes = float(split_dms[1])
        dd = degrees + minutes / 60
        if direction in ['S', 'W']:
            dd *= -1
        return dd

    def changeepsg(self, epsg_code):
        self.transformer = Transformer.from_crs("epsg:4326", epsg_code, always_xy=True)

    def convert_to_plane_coordinate(self, latitude, lat_dir, longitude, lon_dir):
        """转换经纬度为平面坐标系坐标"""
        lat_dd = self.dms_to_dd(latitude, lat_dir)
        lon_dd = self.dms_to_dd(longitude, lon_dir)
        easting, northing = self.transformer.transform(lon_dd, lat_dd)
        return lat_dd, lon_dd, easting, northing


    def close_port(self):
        """关闭串口连接"""
        if self.ser:
            self.ser.close()


if __name__ == '__main__':
    # 使用示例
    gps_reader = RTKGPSReader()  # 替换为你的串口
    gps_reader.open_port('/dev/ttyUSB0', 9600)

    try:
        while True:
            line = gps_reader.read_line()
            print(line)
            data = gps_reader.parse_line(line)
            if data:
                print(data)

                lat_dd, lon_dd, easting, northing = gps_reader.convert_to_plane_coordinate(data['latitude'], data['latitude_direction'], data['longitude'], data['longitude_direction'])
                print(f"Easting: {easting}, Northing: {northing}")

    finally:
        gps_reader.close_port()
