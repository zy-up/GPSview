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

class MyApp(App):
    def __init__(self, ser, position_queue, **kwargs):
        super().__init__(**kwargs)
        self.stop_event = threading.Event()
        self.position_queue = position_queue
        self.ser = ser
        self.data = {'time': '0',
                    'latitude': '0',
                    'latitude_direction': '0',
                    'longitude': '0',
                    'longitude_direction': '0',
                    'fix_quality': '0',
                    'num_satellites': '0',
                    'horizontal_dilution': '0',
                    'altitude': '0',
                    'altitude_units': '0',
                    'geoidal_separation': '0',
                    'geoidal_units': '0',
                    'age_of_diff_corr': '0',}
        self.lat_dd, self.lon_dd, self.easting, self.northing = None,None,None,None
        
        
    def build(self):
        # 创建根布局
        self.root = BoxLayout(orientation='horizontal', padding=15)
        
        # 创建GPS基础信息
        self.gps_info = BoxLayout(orientation='vertical', size_hint_x=None, width=300, spacing=10)
        
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
        self.plane_system_section.add_widget(self.EPSG)
        # X
        self.plane_system_section.add_widget(Label(text='X:', font_size='20sp'))
        self.X = Label(text='0', font_size='20sp')
        self.plane_system_section.add_widget(self.X)
        # Y
        self.plane_system_section.add_widget(Label(text='Y:', font_size='20sp'))
        self.Y = Label(text='0', font_size='20sp')
        self.plane_system_section.add_widget(self.Y)
        # X_error
        self.plane_system_section.add_widget(Label(text='X_error:', font_size='20sp'))
        self.X_error = Label(text='0', font_size='20sp')
        self.plane_system_section.add_widget(self.X_error)
        # Y_error
        self.plane_system_section.add_widget(Label(text='Y_error:', font_size='20sp'))
        self.Y_error = Label(text='0', font_size='20sp')
        self.plane_system_section.add_widget(self.Y_error)

        # 将各部分的布局添加到左侧面板
        self.gps_info.add_widget(Label(text='Serial Setting', font_size='25sp'))
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
        self.filter_section.add_widget(Label(text='DGPS:', font_size='20sp'))
        self.DGPS = CheckBox(active=True)
        self.filter_section.add_widget(self.DGPS)
        # 是否过滤Float状态数据
        self.filter_section.add_widget(Label(text='Float:', font_size='20sp'))
        self.Float = CheckBox(active=True)
        self.filter_section.add_widget(self.Float)
        # 是否过滤Fixed状态数据
        self.filter_section.add_widget(Label(text='Fixed:', font_size='20sp'))
        self.Fixed = CheckBox(active=True)
        self.filter_section.add_widget(self.Fixed)
        # 过滤误差过大的值
        self.filter_section.add_widget(Label(text='XY_Error:', font_size='20sp'))
        self.XY_Error = TextInput(text='0', font_size='20sp')
        self.filter_section.add_widget(self.XY_Error)

        # 用于记录GPS数据
        self.recorder_section = GridLayout(cols=2, size_hint_y=None, height=80, size_hint_x=None, width=300)
        # 过滤误差过大的值
        self.recorder_section.add_widget(Label(text='Num:', font_size='20sp'))
        self.Num = TextInput(text='200', font_size='20sp')
        self.recorder_section.add_widget(self.Num)
        # 过滤误差过大的值
        self.recorder_section.add_widget(Label(text='Name:', font_size='20sp'))
        self.Name = TextInput(text='2023', font_size='20sp')
        self.recorder_section.add_widget(self.Name)

        self.gps_Recorder.add_widget(Label(text='GPS filter', font_size='25sp'))
        self.gps_Recorder.add_widget(self.filter_section)
        self.gps_Recorder.add_widget(Label(text='GPS Recorder', font_size='25sp'))
        self.gps_Recorder.add_widget(self.recorder_section)
        self.Recorder_Button = Button(text='Start', size_hint_x=None, width=300, background_color=(0, 1, 0, 1), padding=1, font_size='20sp')
        self.gps_Recorder.add_widget(self.Recorder_Button)
        self.gps_Recorder.add_widget(Label(text='', font_size='25sp'))

        self.map_section = BoxLayout(orientation='vertical', padding=10)
        map_source = MapSource(url="https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}", attribution="© Google Maps")
        self.map_view = MapView(map_source=map_source, zoom=18, lat=35.176148385, lon=126.90049612)
        self.marker = MapMarker(lat=35.176148385, lon=126.90049612, source=r'GPS\Point.png')
        self.map_view.add_marker(self.marker)
        self.map_section.add_widget(self.map_view)
        
        # 将左侧面板和地图显示部分添加到根布局
        self.root.add_widget(self.gps_info)
        self.root.add_widget(self.gps_Recorder)
        self.root.add_widget(self.map_section)

        self.update_serial_ports()


        # 使用 Kivy 的 Clock 模块每隔一段时间调用更新函数
        Clock.schedule_interval(self.update_data, 0.1)  # 每秒更新一次

        return self.root

    def update_data(self, *args):
        if not self.position_queue.empty():
            self.data, self.lat_dd, self.lon_dd, self.easting, self.northing = self.position_queue.get_nowait()

        if self.lat_dd is not None and self.lon_dd is not None:
            self.marker.lat = str(self.lat_dd)
            self.marker.lon = str(self.lon_dd)

            self.Satellites.text = self.data['num_satellites']
            self.State.text = self.data['fix_quality']
            self.Altitude.text = self.data['altitude']

            self.Longitude.text = str(self.lon_dd)
            self.Latitude.text = str(self.lat_dd)

            self.X.text = str(self.easting)
            self.Y.text = str(self.northing)

            # 强制刷新地图
            self.map_view.center_on(self.lat_dd, self.lon_dd)

        pass

    def update_serial_ports(self):
        """检测并更新可用的串口列表"""
        ports = serial.tools.list_ports.comports()
        available_ports = [port.device for port in ports]
        self.serial_spinner.values = available_ports

    def toggle_serial_port(self, instance):
        selected_port = self.serial_spinner.text
        print("开启或关闭选定的串口")
        if selected_port != 'Select Port':
            if instance.text == 'Start':
                print(selected_port)
                self.ser = serial.Serial(selected_port, 9600)
                instance.text = 'Stop'
            else:
                if self.ser:
                    self.ser.close()
                # 在这里编写关闭串口的代码
                instance.text = 'Start'

    def on_stop(self):
        # 应用关闭时触发
        self.stop_event.set()  # 通知其他线程停止

if __name__ == '__main__':
    MyApp().run()
