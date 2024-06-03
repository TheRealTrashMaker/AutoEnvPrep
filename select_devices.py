# _*_ coding : UTF-8 _*_
# @Time : 2024/5/21 上午10:54
# @Auther : TrashMaker
# @File : AutoInstaller
# @Project : AutoInstaller
# @Desc :AutoInstaller
from ppadb.client import Client as AdbClient


def device_rec(deviceid):
    """
        pass
    """
    client = AdbClient(host="127.0.0.1", port=5037)
    device = client.device(deviceid)
    try:
        res = device.shell("getprop ro.product.model")
    except:
        res = "unknown"
    print(res)
    return res


if __name__ == '__main__':
    res = device_rec('192.168.0.237:5555')
    print(res)
