from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.checkbox import CheckBox
from kivy.garden.mapview import MapView, MapMarker, MapSource
from kivy.clock import Clock

import threading
import serial
import serial.tools.list_ports

import os
import logging
from datetime import datetime

from collections import deque

class MyApp(App):
    def __init__(self, ser, GPS_info_queue, Setting_queue, **kwargs):
        super().__init__(**kwargs)
        # 程序结束时间标志
        self.stop_event = threading.Event()

        # 接收句柄与压栈参数
        self.ser = ser
        self.GPS_info_queue = GPS_info_queue
        self.Setting_queue = Setting_queue
        
        # 初始化参数
        self.data = {'time': '0','latitude': '0','latitude_direction': '0','longitude': '0','longitude_direction': '0','fix_quality': '0','num_satellites': '0',
                    'horizontal_dilution': '0','altitude': '0','altitude_units': '0',
                    'geoidal_separation': '0','geoidal_units': '0','age_of_diff_corr': '0',}
        self.lat_dd, self.lon_dd, self.easting, self.northing = None,None,None,None

        # 录制GPS点信息参数
        self.RecorderFlag = 0

        # 初始化一个固定大小为20的deque
        self.x_history = deque(maxlen=20)
        self.y_history = deque(maxlen=20)
        
        
    def build(self):
        # 创建根布局
        self.root = BoxLayout(orientation='horizontal', padding=15)
        
        # 创建GPS基础信息
        self.gps_info = BoxLayout(orientation='vertical', size_hint_x=None, width=300, spacing=10, )
        
        # 创建串口部分的布局
        self.serial_section = BoxLayout(orientation='vertical', size_hint_y=None, height=120,size_hint_x=None, width=300)
        self.serial_spinner = Spinner(text='Select Port', size_hint_x=None, width=300, background_color=(0, 1, 0, 1), padding=1, font_size='20sp')
        self.serial_button = Button(text='Start', size_hint_x=None, width=300, background_color=(0, 0, 1, 1), padding=1, font_size='20sp')
        self.serial_section.add_widget(self.serial_spinner)
        self.serial_section.add_widget(self.serial_button)
        self.serial_button.bind(on_press=self.toggle_serial_port)

        # 创建GPS原始数据部分的布局
        self.gps_state_section = GridLayout(cols=2, size_hint_y=None, height=200, size_hint_x=None, width=300)

        # 卫星数量标签
        self.gps_state_section.add_widget(Label(text='Satellites:', font_size='20sp'))
        self.Satellites = Label(text='0', font_size='20sp')
        self.gps_state_section.add_widget(self.Satellites)
        # GPS状态标签
        self.gps_state_section.add_widget(Label(text='State:', font_size='20sp'))
        self.State = Label(text='0', font_size='20sp')
        self.gps_state_section.add_widget(self.State)
        # 经度数量标签
        self.gps_state_section.add_widget(Label(text='Longitude:', font_size='20sp'))
        self.Longitude = Label(text='0', font_size='20sp')
        self.gps_state_section.add_widget(self.Longitude)
        # 维度数量标签
        self.gps_state_section.add_widget(Label(text='Latitude:', font_size='20sp'))
        self.Latitude = Label(text='0', font_size='20sp')
        self.gps_state_section.add_widget(self.Latitude)
        # 海拔数量标签
        self.gps_state_section.add_widget(Label(text='Altitude:', font_size='20sp'))
        self.Altitude = Label(text='0', font_size='20sp')
        self.gps_state_section.add_widget(self.Altitude)
        
        # 将经纬度转化为平面坐标
        self.plane_system_section = GridLayout(cols=2, size_hint_y=None, height=200, size_hint_x=None, width=300)
        # 选择平面坐标系
        self.plane_system_section.add_widget(Label(text='EPSG:', font_size='20sp'))
        self.EPSG = TextInput(text='5186', font_size='20sp')
        self.EPSG.bind(text=self.on_textinput_EPSG)  # 绑定事件处理函数
        self.plane_system_section.add_widget(self.EPSG)
        # X
        self.plane_system_section.add_widget(Label(text='X(m):', font_size='20sp'))
        self.X = Label(text='0', font_size='20sp')
        self.plane_system_section.add_widget(self.X)
        # Y
        self.plane_system_section.add_widget(Label(text='Y(m):', font_size='20sp'))
        self.Y = Label(text='0', font_size='20sp')
        self.plane_system_section.add_widget(self.Y)
        # X_error
        self.plane_system_section.add_widget(Label(text='X_error(m):', font_size='20sp'))
        self.X_error = Label(text='0', font_size='20sp')
        self.plane_system_section.add_widget(self.X_error)
        # Y_error
        self.plane_system_section.add_widget(Label(text='Y_error(m):', font_size='20sp'))
        self.Y_error = Label(text='0', font_size='20sp')
        self.plane_system_section.add_widget(self.Y_error)

        # 将各部分的布局添加到左侧面板
        # self.gps_info.add_widget(Label(text='Serial Setting', font_size='25sp'))
        self.gps_info.add_widget(self.serial_section)
        self.gps_info.add_widget(Label(text='', width=40, font_size='25sp'))
        self.gps_info.add_widget(Label(text='GPS State:', width=40, font_size='25sp'))
        self.gps_info.add_widget(self.gps_state_section)
        self.gps_info.add_widget(Label(text='', width=40, font_size='25sp'))
        self.gps_info.add_widget(Label(text='Plane-co system', width=40, font_size='25sp'))
        self.gps_info.add_widget(self.plane_system_section)
        self.gps_info.add_widget(Label(text='', width=40, font_size='25sp'))

        # 用于过滤GPS数据
        self.gps_Recorder = BoxLayout(orientation='vertical', size_hint_x=None, width=300, spacing=10)
        self.filter_section = GridLayout(cols=2, size_hint_y=None, height=180, size_hint_x=None, width=300)
        # 是否过滤DGPS状态数据
        self.filter_section.add_widget(Label(text='DGPS (2):', font_size='20sp'))
        self.DGPS = CheckBox(active=True)
        self.DGPS.bind(active=self.on_checkbox_active)  # 绑定事件处理函数
        self.filter_section.add_widget(self.DGPS)
        # 是否过滤Float状态数据
        self.filter_section.add_widget(Label(text='Float (4):', font_size='20sp'))
        self.Float = CheckBox(active=True)
        self.Float.bind(active=self.on_checkbox_active)  # 绑定事件处理函数
        self.filter_section.add_widget(self.Float)
        # 是否过滤Fixed状态数据
        self.filter_section.add_widget(Label(text='Fixed (5):', font_size='20sp'))
        self.Fixed = CheckBox(active=True)
        self.Fixed.bind(active=self.on_checkbox_active)  # 绑定事件处理函数
        self.filter_section.add_widget(self.Fixed)
        # 过滤误差过大的值
        self.filter_section.add_widget(Label(text='XY_Error:', font_size='20sp'))
        self.XY_Error = TextInput(text='0', font_size='20sp')
        self.XY_Error.bind(text=self.on_textinput_XYerror)  # 绑定事件处理函数
        self.filter_section.add_widget(self.XY_Error)

        # 用于记录GPS数据
        self.recorder_section = GridLayout(cols=2, size_hint_y=None, height=80, size_hint_x=None, width=300)
        # 过滤误差过大的值
        self.recorder_section.add_widget(Label(text='Num:', font_size='20sp'))
        self.Num = TextInput(text='25', font_size='20sp')
        self.recorder_section.add_widget(self.Num)
        # 过滤误差过大的值
        self.recorder_section.add_widget(Label(text='Name:', font_size='20sp'))
        self.Name = TextInput(text='L1_1', font_size='20sp')
        self.recorder_section.add_widget(self.Name)

        self.gps_Recorder.add_widget(Label(text='GPS filter', font_size='25sp'))
        self.gps_Recorder.add_widget(self.filter_section)
        self.gps_Recorder.add_widget(Label(text='GPS Recorder', font_size='25sp'))
        self.gps_Recorder.add_widget(self.recorder_section)
        self.Recorder_Button = Button(text='Start', size_hint_x=None, width=300, background_color=(0, 1, 0, 1), padding=1, font_size='20sp')
        self.Recorder_Button.bind(on_press=self.RecorderAction)
        self.gps_Recorder.add_widget(self.Recorder_Button)
        self.gps_Recorder.add_widget(Label(text='', font_size='25sp'))

        # 添加地图显示
        self.map_section = BoxLayout(orientation='vertical', padding=10)
        map_source = MapSource(url="https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}", attribution="© Google Maps")
        self.map_view = MapView(map_source=map_source, zoom=18, lat=35.176148385, lon=126.90049612)
        self.marker = MapMarker(lat=35.176148385, lon=126.90049612, source='Point.png')
        self.map_view.add_marker(self.marker)
        self.map_section.add_widget(self.map_view)
        
        # 将左侧面板和地图显示部分添加到根布局
        self.root.add_widget(self.gps_info)
        self.root.add_widget(self.gps_Recorder)
        self.root.add_widget(self.map_section)

        # 检索当前的所有串口
        self.update_serial_ports()

        # 使用 Kivy 的 Clock 模块每隔一段时间调用更新函数
        Clock.schedule_interval(self.update_data, 0.1)  # 10HZ更新
        
        return self.root


    def setup_GPSpoint_logger(self, name):
        # 设置自定义日志记录器
        current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        log_directory = "./log"
        if not os.path.exists(log_directory):
            os.makedirs(log_directory)
        log_filename = f"{log_directory}/GPS_log_{current_time}_{self.Name.text}.log"

        # 创建一个自定义的日志记录器
        logger = logging.getLogger(name)
        logger.setLevel(logging.INFO)

        # 创建文件处理器
        file_handler = logging.FileHandler(log_filename)
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

        # 将处理器添加到日志记录器
        logger.addHandler(file_handler)

        return logger


    # 执行GPS点的录制
    def RecorderAction(self, instance):
            if instance.text == 'Start' and self.ser.is_open:
                # 标志置1，送出录制信号
                self.RecorderFlag = 1
                instance.text = 'Doing'

                self.GPSlogger = self.setup_GPSpoint_logger("MyAppLogger")
                self.GPSlogger.info("This is an info message.")
            else:
                print("串口未打开")


    # 定时更新数据
    def update_data(self, *args):
        # 检查是否有数据更新
        if not self.GPS_info_queue.empty():
            self.data, self.lat_dd, self.lon_dd, self.easting, self.northing = self.GPS_info_queue.get_nowait()

        # if self.lat_dd is not None and self.lon_dd is not None:
            self.marker.lat = str(self.lat_dd)
            self.marker.lon = str(self.lon_dd)

            self.Satellites.text = str(self.data['num_satellites'])
            self.State.text = str(self.data['fix_quality'])
            self.Altitude.text = str(self.data['altitude'])

            self.Longitude.text = "{:.4f}".format(self.lat_dd)
            self.Latitude.text = "{:.4f}".format(self.lon_dd)

            self.X.text = "{:.4f}".format(self.easting)
            self.Y.text = "{:.4f}".format(self.northing)

            self.x_history.append(self.easting)
            self.y_history.append(self.northing)

            # 计算XY平均误差
            if len(self.x_history) == 20:
                x_average_past = sum(self.x_history) / len(self.x_history)
                x_error = self.easting - x_average_past
                self.X_error.text = "{:.4f}".format(x_error)

                y_average_past = sum(self.y_history) / len(self.y_history)
                y_error = self.northing - y_average_past
                self.Y_error.text = "{:.4f}".format(y_error)

            # 强制刷新地图
            self.map_view.center_on(self.lat_dd, self.lon_dd)

            # 如果RecorderFlag置1，开始录制
            if self.RecorderFlag:
                log_message = f"Data: {self.data}, Latitude: {self.lat_dd}, Longitude: {self.lon_dd}, Easting: {self.easting}, Northing: {self.northing}"
                self.GPSlogger.info(log_message)
                self.RecorderFlag+=1
                if self.RecorderFlag == int(self.Num.text):
                    self.RecorderFlag = 0
                    self.Recorder_Button.text = 'Start'

    
    # 检测当前的可用端口
    def update_serial_ports(self):
        """检测并更新可用的串口列表"""
        ports = serial.tools.list_ports.comports()
        available_ports = [port.device for port in ports]
        self.serial_spinner.values = available_ports

    # 串口开启或关闭
    def toggle_serial_port(self, instance):
        selected_port = self.serial_spinner.text
        print("开启或关闭选定的串口：")
        if selected_port != 'Select Port':
            if instance.text == 'Start':
                print(selected_port)
                try:
                    self.ser.port = selected_port
                    self.ser.baudrate = 9600
                    self.ser.open()
                    instance.text = 'Stop'
                except:
                    print("打开失败")
                    return 0

                self.Setting_queue.put(self.EPSG.text)
            else:
                if self.ser:
                    self.ser.close()
                # 在这里编写关闭串口的代码
                instance.text = 'Start'
        else:
            self.update_serial_ports()
            print("选择有效端口")

    def on_stop(self):
        # 应用关闭时触发
        self.stop_event.set()  # 通知其他线程停止

    def on_checkbox_active(self, checkbox, value):
        # 处理复选框状态更改
        print(f'Checkbox {checkbox} is {"active" if value else "inactive"}')
        
    def on_textinput_XYerror(self, instance, value):
        # 处理文本输入更改
        print(f'Textinput value: {value}')

    def on_textinput_EPSG(self, instance, value):
        # 处理文本输入更改
        print(f'Textinput value: {value}')


if __name__ == '__main__':
    MyApp().run()
