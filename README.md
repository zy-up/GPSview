# GPSview

## 安装依赖
```bash
pip inatall requirements.txt
```

### 检查 mapview 的安装
确保您已安装 mapview 组件。可以通过 Kivy Garden 工具安装它，如果您还没有这样做：

```bash
garden install mapview
```
如果遇到“Permission denied”的报错
1. Check Permissions:
```bash
chmod +x /home/sibl/anaconda3/envs/geo/bin/garden
```
2. Check Installation Directory:
```bash
sudo chmod o+w /path/to/installation/directory
```

## 运行主函数

```bash
python /scripts/main.py
```

