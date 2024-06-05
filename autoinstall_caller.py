import re
import subprocess
import threading

from ppadb.client import Client as AdbClient

from install import AutoInstall


def is_connected_vpn(device, device_id):
    """
    是否已连接VPN
    :return:
    """
    try:
        res = device.shell('ifconfig | grep "inet addr"')
        reg = r'inet addr:(\d+.\d+.\d+.\d+)'
        address = re.findall(reg, res)
        if len(address) == 3:
            vpn_ip = address[0]
            adr_ip = address[2]
        elif len(address) == 2:
            vpn_ip = "0.0.0.0"
            adr_ip = address[1]
        return {adr_ip: vpn_ip}
    except:
        return {device_id[0:-5]: "offline"}


def get_vpn_list():
    devices_vpn_list = []
    output = subprocess.check_output(['adb', 'devices']).decode('utf-8')
    client = AdbClient(host="127.0.0.1", port=5037)

    # 按行循环处理输出
    for line in output.split('\n')[0:-2]:
        if 'List of devices attached' in line or not line:
            continue
        # 提取设备ip地址
        ip = line.split('\t')[0]
        device_id = (f"{ip}")
        # print("device_id----",device_id)
        device = client.device(device_id)
        try:
            res = is_connected_vpn(device, device_id=device_id)
            devices_vpn_list.append(res)
        except:
            pass
    return devices_vpn_list


def screen_wake(device):
    """
    唤醒/息屏设备
    """
    # KEYCODE_SLEEP 休眠
    # KEYCODE_WAKEUP 唤醒

    device.shell('input keyevent KEYCODE_WAKEUP', timeout=5)


def get_devices_list():
    output = subprocess.check_output(['adb', 'devices']).decode('utf-8')
    client = AdbClient(host="127.0.0.1", port=5037)
    devices_list = []
    offline_list = []
    # 按行循环处理输出
    for line in output.split('\n')[0:-2]:
        if 'List of devices attached' in line or not line:
            continue
        # 提取设备ip地址
        ip = line.split('\t')[0]
        device_id = (f"{ip}")
        print(device_id)
        device = client.device(device_id)
        print(device_id)
        try:
            screen_wake(device)
            print(device_id)
            devices_list.append(device_id)
        except:
            offline_list.append(device_id)
    return devices_list, offline_list


def auto_install_runner(device_id, data):
    auto_ins = AutoInstall(device_id=device_id, data=data)
    # auto_ins.software_version_ctrl()
    # auto_ins.change_font()
    # auto_ins.change_eage()
    # auto_ins.eage_ready()
    #auto_ins.install_req()
    auto_ins.screen_wake()
    auto_ins.change_vpn(data)
    # auto_ins.device.shell("input keyevent KEYCODE_HOME")


if __name__ == '__main__':
    vpn_list = []
    for i in range(253):
        vpn_list.append({"vpn_url": "107.148.0.101:943", "vpn_acc": "wang" + f"{i+1:04d}", "vpn_pwd": "888866666"})
    devices_list, offline_list = get_devices_list()
    # for i in range(len(devices_list)):
    #     #data = {"vpn_url": "108.186.154.79:943", "vpn_acc": "zhang0" + str(i + 20), "vpn_pwd": "888555222"}
    #     ther = threading.Thread(target=auto_install_runner, args=(i, vpn_list[i]))
    #     ther.start()
    x = 0
    for i in devices_list:

        ther = threading.Thread(target=auto_install_runner, args=(i, vpn_list[x]))
        ther.start()
        x = x + 1
        print(i)


    # lister = ['192.168.11.217:5555',
    #           '192.168.11.89:5555',
    #           '192.168.11.191:5555',
    #           '192.168.11.178:5555',
    #           '192.168.11.216:5555',
    #           '192.168.11.207:5555',
    #           '192.168.11.213:5555',
    #           '192.168.11.105:5555',
    #           '192.168.11.117:5555',
    #           '192.168.11.110:5555',
    #           '192.168.11.11:5555',
    #           '192.168.11.199:5555',
    #           '192.168.11.163:5555',
    #           '192.168.11.120:5555',
    #           '192.168.11.204:5555',
    #           '192.168.11.27:5555',
    #           '192.168.11.239:5555',
    #           '192.168.11.144:5555',
    #           '192.168.11.40:5555',
    #           '192.168.11.126:5555',
    #           '192.168.11.101:5555',
    #           '192.168.11.72:5555', ]
    # for i in range(len(lister)):
    #     data = {"vpn_url": "108.186.154.79:943", "vpn_acc": "zhang0" + str(i + 20), "vpn_pwd": "888555222"}
    #     ther = threading.Thread(target=auto_install_runner, args=(lister[i], data))
    #     ther.start()
