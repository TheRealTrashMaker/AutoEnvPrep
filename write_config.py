import configparser

# 创建ConfigParser对象
config = configparser.ConfigParser()
# 添加section和键值对
config.add_section('package_name')
config.add_section('Section1')
config.set('package_name', 'tiktok', 'com.zhiliaoapp.musically')
config.set('package_name', 'chrome116', 'org.chromium.chrome')
config.set('package_name', 'chrome125', 'com.android.chrome')
config.set('package_name', 'openvpn324', 'net.openvpn.openvpn')
config.set('package_name', 'openvpn342', 'net.openvpn.openvpn')
#config.set('Section1', 'key2', 'value2')

# 写入到文件
with open('config.ini', 'w') as configfile:
    config.write(configfile)
print("INI文件写入成功")