from pyproj import Transformer
import re

# 定义转换度分格式为十进制度的函数
def dms_to_dd(dms, direction):
    # 将字符串分割为度和分
    split_dms = re.split(r'(\d+)(\d{2}\.\d+)', dms)
    # 去除空字符串项
    split_dms = list(filter(None, split_dms))
    # 分别得到度和分的值
    degrees = float(split_dms[0])
    minutes = float(split_dms[1])
    # 转换为十进制度
    dd = degrees + minutes / 60
    # 如果方向为南或西，结果为负
    if direction in ['S', 'W']:
        dd *= -1
    return dd

# 测试代码
lat_dms = "3510.5689031"
lat_dir = "N"
lon_dms = "12654.0297672"
lon_dir = "E"

# 转换为十进制度
lat_dd = dms_to_dd(lat_dms, lat_dir)
lon_dd = dms_to_dd(lon_dms, lon_dir)


print("lat_dd (X):", lat_dd)
print("lon_dd (Y):", lon_dd)

# 创建坐标转换器
transformer = Transformer.from_crs("epsg:4326", "epsg:5186", always_xy=True)

# 转换坐标
easting, northing = transformer.transform(lon_dd, lat_dd)

print("Korea 2000 / Central Belt Coordinates:")
print("Easting (X):", easting)
print("Northing (Y):", northing)








