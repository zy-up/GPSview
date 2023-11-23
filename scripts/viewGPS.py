# -*- coding: utf-8 -*-
from kivy.app import App
from kivy.garden.mapview import MapView, MapMarker, MapSource
from kivy.clock import Clock
from queue import Queue 

class SatelliteMapApp(App):
    def __init__(self, position_queue, **kwargs):
        super().__init__(**kwargs)
        self.position_queue = position_queue
        self.last_known_position = (35.176148385, 126.90049612)  # 初始位置

    def update_marker_position(self, *args):
        # 这里获取新的位置数据，例如从 GPS 或其他源
        new_lat, new_lon = self.get_new_position()

        if new_lat is not None and new_lon is not None:
            self.marker.lat = new_lat
            self.marker.lon = new_lon

            # 强制刷新地图
            self.map_view.center_on(new_lat, new_lon)

    def get_new_position(self):
        # 如果队列中有新的位置数据，则更新最后已知的位置
        if not self.position_queue.empty():
            self.last_known_position = self.position_queue.get_nowait()
        
        return self.last_known_position  # 始终返回最后已知的位置

    def build(self):
        map_source = MapSource(url="https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}", attribution="© Google Maps")
        self.map_view = MapView(map_source=map_source, zoom=18, lat=35.176148385, lon=126.90049612)
        self.marker = MapMarker(lat=35.176148385, lon=126.90049612, source=r'/home/sbdx/Codes/Daily_Code/GPS/Point.png')
        self.map_view.add_marker(self.marker)

        # 使用 Kivy 的 Clock 模块每隔一段时间调用更新函数
        Clock.schedule_interval(self.update_marker_position, 0.1)  # 每秒更新一次

        return self.map_view

if __name__ == '__main__':
    position_queue = Queue()
    SatelliteMapApp(position_queue).run()