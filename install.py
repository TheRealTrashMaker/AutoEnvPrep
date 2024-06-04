# _*_ coding : UTF-8 _*_
# @Time : 2024/5/24 下午16:50
# @Auther : TrashMaker
# @File : AutoInstaller
# @Project : AutoInstaller
# @Desc :AutoInstaller
import configparser
import os.path
import re
import time
import uuid

from lxml import etree
from ppadb.client import Client as AdbClient

from ovpn import get_vpn_profile
from select_devices import device_rec
from util.logger import logger


class AutoInstall:
    def __init__(self, device_id, data):
        """
        初始化 语言,机型,软件版本 等设置
        :param device_id:
        :param data:
        """
        self.config = configparser.ConfigParser()
        self.req_path = os.path.join(os.getcwd(), 'req')
        self.config.read('config.ini')
        self.client = AdbClient(host="127.0.0.1", port=5037)
        self.device = self.client.device(device_id)
        self.device_name = device_rec(device_id)
        self.device_id = device_id
        self.device.shell(f"push {self.req_path}/yadb /data/local/tmp")
        self.data = data
        self.totle_lang = "JP"
        if self.totle_lang == "JP":
            self.totle_time_zone = "Asia/Tokyo"
        else:
            self.totle_time_zone = None
        self.device.shell("settings put system accelerometer_rotation 0")
        self.lang = self.get_device_language()
        self.device_sdk_version = self.device.shell("getprop ro.build.version.sdk")
        self.device.shell("settings put global auto_time 1")  # 设置时间自动同步
        if "SM-G955F" in self.device_name and "24" in self.device_sdk_version:
            logger.info(f"{self.device_id}: 支持的机型: SM-G955F,sdk版本：{self.device_sdk_version}")
            self.settings = {
                "device_name": "SM-G955F",
                "chrome": "chrome116",
                "openvpn": "openvpn324",
                "tiktok": "tiktok"
            }

            self.software_version_settings = {
                "tiktok": self.config.get("software_version_by_sdk24", "tiktok"),
                "openvpn": self.config.get("software_version_by_sdk24", "openvpn"),
                "chrome": self.config.get("software_version_by_sdk24", "chrome")
            }
        elif "SM-G950U" in self.device_name and "28" in self.device_sdk_version:
            logger.info(f"{self.device_id}: 支持的机型: SM-G950U,sdk版本：{self.device_sdk_version}")
            self.settings = {
                "device_name": "SM-G950U",
                "chrome": "chrome125",
                "openvpn": "openvpn342",
                "tiktok": "tiktok"
            }
            self.software_version_settings = {
                "tiktok": self.config.get("software_version_by_sdk28", "tiktok"),
                "openvpn": self.config.get("software_version_by_sdk28", "openvpn"),
                "chrome": self.config.get("software_version_by_sdk28", "chrome")
            }
        elif "SM-G955F" not in self.device_name and "24" in self.device_sdk_version:
            logger.warning(
                f"{self.device_id}: 不支持的机型: {self.device_name},sdk版本：{self.device_sdk_version},sdk版本有对应软件")
            self.settings = {
                "device_name": self.device_name,
                "chrome": "chrome116",
                "openvpn": "openvpn324",
                "tiktok": "tiktok"
            }

            self.software_version_settings = {
                "tiktok": self.config.get("software_version_by_sdk24", "tiktok"),
                "openvpn": self.config.get("software_version_by_sdk24", "openvpn"),
                "chrome": self.config.get("software_version_by_sdk24", "chrome")
            }
        else:
            logger.error(
                f"{self.device_id}:不支持的机型:{self.device_name},sdk版本:{self.device_sdk_version},有可能出现问题")
            self.settings = {
                "device_name": "unknown",
                "chrome": "chrome125",
                "openvpn": "openvpn342",
                "tiktok": "tiktok"
            }
            self.software_version_settings = {
                "tiktok": self.config.get("software_version_by_others", "tiktok"),
                "openvpn": self.config.get("software_version_by_others", "openvpn"),
                "chrome": self.config.get("software_version_by_others", "chrome")
            }
        self.init_software_info()  # 初始化软件版本信息

    def init_software_info(self):
        """
        初始化设备安装的软件版本信息
        tiktok, openvpn, chrome等
        """
        # version_release = self.device.shell("getprop ro.build.version.release")
        # version_sdk = self.device.shell("getprop ro.build.version.sdk")
        # product_model = self.device.shell("getprop ro.product.model")
        # product_brand = self.device.shell("getprop ro.product.brand")
        # wm_size = self.device.shell("wm size")
        # language = self.device.shell("getprop persist.sys.locale")

        if self.device.is_installed("com.android.chrome"):
            chrome_version = self.device.shell(f"dumpsys package com.android.chrome | grep versionName")
            chrome_version = re.search(r"versionName=(.*)", chrome_version).group(1)
            self.chrome_version = chrome_version
        elif self.device.is_installed("org.chromium.chrome"):
            chrome_version = self.device.shell(f"dumpsys package org.chromium.chrome | grep versionName")
            chrome_version = re.search(r"versionName=(.*)", chrome_version).group(1)
            self.chrome_version = chrome_version
        else:
            self.chrome_version = ""

        if self.device.is_installed("com.zhiliaoapp.musically"):
            tiktok_version = self.device.shell(f"dumpsys package com.zhiliaoapp.musically | grep versionName")
            tiktok_version = re.search(r"versionName=(.*)", tiktok_version).group(1)
            self.tiktok_version = tiktok_version
        else:
            self.tiktok_version = ""
        if self.device.is_installed("net.openvpn.openvpn"):
            openvpn_version = self.device.shell(f"dumpsys package net.openvpn.openvpn | grep versionName")
            openvpn_version = re.search(r"versionName=(.*)", openvpn_version).group(1)
            self.openvpn_version = openvpn_version
        else:
            self.openvpn_version = ""
        # vpn_state = AutoOperation(device).is_connected_vpn()
        # return {
        #     # "设备序列号": device.serial,
        #     # "设备SerialNo": device.get_serial_no(),
        #     "安卓系统版本": version_release.strip(),
        #     "SDK版本": version_sdk.strip(),
        #     "设备型号": product_model.strip(),
        #     "厂商名称": product_brand.strip(),
        #     "分辨率": wm_size.strip().replace("\n", ""),
        #     "设备语言": language.strip(),
        #     "Chrome版本": chrome_version,
        #     "TikTok版本": tiktok_version,
        #     "OpenVPN版本": openvpn_version,
        #     # "VPN状态": vpn_state
        # }

    def is_installed(self, package):
        """
        判断软件是否安装
        :param package:
        :return:
        """
        if self.device.shell(f"pm list packages | grep {package}") != "":
            return True
        else:
            return False

    def get_ui_xml(self):
        """
        获取当前的UI树信息
        :return: lxml解析后的UI树
        """
        uuid_ = str(uuid.uuid4()) + str(int(time.time() * 1000))
        self.device.shell(
            "app_process -Djava.class.path=/data/local/tmp/yadb /data/local/tmp com.ysbing.yadb.Main -layout")
        # 下载UI树文件
        self.device.pull("/sdcard/yadb_layout_dump.xml",
                         os.path.join(os.getcwd(), "caches", f"{uuid_}.xml"))
        # 解析UI树文件
        return etree.parse(os.path.join(os.getcwd(), "caches", f"{uuid_}.xml"))

    def software_version_ctrl(self):
        """
        控制软件版本，防止版本冲突
        :return:
        """
        packages = self.device.shell("pm list packages")
        tiktok = self.settings["tiktok"]
        openvpn = self.settings["openvpn"]
        chrome = self.settings["chrome"]
        if "com.zhiliaoapp.musically" in packages:
            try:
                logger.info(
                    f"设备{self.device_id}: 检测到已安装TikTok，版本为:{self.tiktok_version},需求版本为:{self.software_version_settings['tiktok']}")
                if self.software_version_settings["tiktok"] == self.tiktok_version:
                    logger.info(f"设备{self.device_id}: tiktok 需求版本与已经安装版本一致,无需再次安装")
                else:
                    self.device.shell("pm uninstall com.zhiliaoapp.musically")
                    logger.info(f"设备{self.device_id}: TikTok版本与需求不一致,卸载完成")
                    logger.info(f"设备{self.device_id}--正在安装TikTok")
                    os.system(f"adb -s {self.device_id} install {os.path.join(os.getcwd(), 'req', f'{tiktok}.apk')}")
            except:
                logger.error(f"设备{self.device_id}: TikTok,版本管理失败")
        if "com.android.chrome" in packages:
            try:
                logger.info(
                    f"设备{self.device_id}: 检测到已安装chrome，版本为:{self.chrome_version},需求版本为:{self.software_version_settings['chrome']}")
                if self.software_version_settings["chrome"] == self.chrome_version:
                    logger.info(f"设备{self.device_id}: chrome 需求版本与已经安装版本一致,无需再次安装")
                else:
                    self.device.shell("pm uninstall com.android.chrome")
                    logger.info(f"设备{self.device_id}: Chrome，卸载完成")
                    logger.info(f"设备{self.device_id}--正在安装Chrome")
                    os.system(f"adb -s {self.device_id} install {os.path.join(os.getcwd(), 'req', f'{chrome}.apk')}")
                    logger.info(f"设备{self.device_id}--Chrome已完成安装")
            except:
                logger.error(f"设备{self.device_id}: Chrome，版本管理失败")
        if "org.chromium.chrome" in packages:
            try:
                logger.info(
                    f"设备{self.device_id}: 检测到已安装chrome，版本为:{self.chrome_version},需求版本为:{self.software_version_settings['chrome']}")
                if self.software_version_settings["chrome"] == self.chrome_version:
                    logger.info(f"设备{self.device_id}: chrome 需求版本与已经安装版本一致,无需再次安装")
                else:
                    self.device.shell("pm uninstall com.android.chrome")
                    logger.info(f"设备{self.device_id}: Chrome，卸载完成")
                    logger.info(f"设备{self.device_id}--正在安装Chrome")
                    os.system(f"adb -s {self.device_id} install {os.path.join(os.getcwd(), 'req', f'{chrome}.apk')}")
                    logger.info(f"设备{self.device_id}--Chrome已完成安装")
            except:
                logger.error(f"设备{self.device_id}: Chrome，版本管理失败")
        if "net.openvpn.openvpn" in packages:
            try:
                logger.info(
                    f"设备{self.device_id}: 检测到已安装openvpn，版本为:{self.openvpn_version},需求版本为:{self.software_version_settings['openvpn']}")
                if self.software_version_settings["openvpn"] == self.openvpn_version:
                    logger.info(f"设备{self.device_id}: openvpn 需求版本与已经安装版本一致,无需再次安装")
                else:
                    self.device.shell("pm uninstall net.openvpn.openvpn")
                    logger.info(f"设备{self.device_id}: OpenVPN版本不对，卸载完成，等待安装")
                    logger.info(f"设备{self.device_id}--正在安装OpenVPN")
                    os.system(f"adb -s {self.device_id} install {os.path.join(os.getcwd(), 'req', f'{openvpn}.apk')}")
                    logger.info(f"设备{self.device_id}--OpenVPN安装完成")
            except:
                logger.error(f"设备{self.device_id}: OpenVPN，卸载失败")
        else:
            logger.info(
                f"设备{self.device_id}: OpenVPN没有安装，等待安装，需求版本为{self.software_version_settings['openvpn']}")
            logger.info(f"设备{self.device_id}--正在安装OpenVPN")
            os.system(f"adb -s {self.device_id} install {os.path.join(os.getcwd(), 'req', f'{openvpn}.apk')}")
            logger.info(f"设备{self.device_id}--OpenVPN安装完成")
        logger.info(f"设备{self.device_id}: 初始处理完成，准备进行下一步操作")

    def install_req(self):
        """
        安装TikTok，OpenVpn，Chrome
        :param device_id: 设备id（ip:端口号）
        :return:
        """
        try:
            tiktok = self.settings["tiktok"]
            openvpn = self.settings["openvpn"]
            chrome = self.settings["chrome"]
            self.device.shell("input keyevent HOME")
            logger.info(f"设备{self.device_id}--正在安装TikTok")
            os.system(f"adb -s {self.device_id} install {os.path.join(os.getcwd(), 'req', f'{tiktok}.apk')}")
            logger.info(f"设备{self.device_id}--TikTok已完成安装")
            logger.info(f"设备{self.device_id}--正在安装OpenVPN")
            os.system(f"adb -s {self.device_id} install {os.path.join(os.getcwd(), 'req', f'{openvpn}.apk')}")
            logger.info(f"设备{self.device_id}--OpenVPN已完成安装")
            logger.info(f"设备{self.device_id}--正在安装Chrome")
            os.system(f"adb -s {self.device_id} install {os.path.join(os.getcwd(), 'req', f'{chrome}.apk')}")
            logger.info(f"设备{self.device_id}--Chrome已完成安装")
            return True
        except:
            logger.error(f"设备{self.device_id}--安装时出现错误，请介入人工检查")
            return False

    def median_value(self, numer):
        """
        取元素中间值
        :param num:
        :return:
        """
        index_subscript = numer[-1].replace("[", '').replace("]", ' ')
        index_list = index_subscript.split(' ')
        index_1 = index_list[0].split(",")
        index_2 = index_list[1].split(",")
        subscript_x = (int(index_1[0]) + int(index_2[0])) / 2
        subscript_y = (int(index_1[1]) + int(index_2[1])) / 2
        li = f"{subscript_x} {subscript_y}"
        return li

    def element_find_by_text(self, text, type=True):
        """
        根据元素查找坐标点
        成功返回：坐标（list）
        失败返回：False（bool）
        """
        device_xml = self.get_ui_xml()
        if type == True:
            elements = device_xml.xpath(f"//*[@text='{text}']/@bounds")
            add_profile_point = self.median_value_pro(elements)
            return add_profile_point
        elif type == False:
            try:
                elements = device_xml.xpath(f"//*[@text='{text}']/@bounds")
                add_profile_point = self.median_value_pro(elements)
                return add_profile_point
            except:
                return None

    def change_font(self):
        """
        检测更改字体
        :param device_id: 设备id（ip:端口号）
        :return:
        """
        if self.totle_lang == "CN":
            self.device.shell("am start -a android.settings.LOCALE_SETTINGS")
            device_xml = self.get_ui_xml()
            labels = device_xml.xpath('//*[@resource-id="com.android.settings:id/label"]/@content-desc')
            if "简体中文" in labels[0]:
                logger.info(f"设备{self.device_id}--默认语言为中文，无需更换")
            else:
                logger.error(f"设备{self.device_id}:默认语言非中文，需要手动更换")
        elif self.totle_lang == "EN":
            self.device.shell("am start -a android.settings.LOCALE_SETTINGS")
            time.sleep(5)
            device_xml = self.get_ui_xml()
            labels = device_xml.xpath('//*[@resource-id="com.android.settings:id/label"]/@content-desc')
            if "English" in labels[0]:
                logger.info(f"设备{self.device_id}--默认语言为英文，无需更换")
                self.lang = self.totle_lang
            else:
                if "SM-G955F" in self.device_name:
                    if self.is_edit_exist():
                        self.element_click("//*[@text='编辑']/@bounds")
                        time.sleep(3)
                        self.device.input_swipe(start_x=969, start_y=724, end_x=963, end_y=388, duration=500)
                        time.sleep(3)
                        self.device.input_keyevent("BACK")
                        time.sleep(3)
                        self.device.input_keyevent("HOME")
                        logger.info(f"设备{self.device_id}:已更换为英语")
                    else:
                        self.add_language()
                elif "SM-G950U" in self.device_name:
                    if self.is_edit_exist():
                        self.element_click("//*[@text='编辑']/@bounds")
                        time.sleep(3)
                        self.device.input_swipe(start_x=969, start_y=724, end_x=963, end_y=388, duration=500)
                        time.sleep(3)
                        self.device.input_keyevent("BACK")
                        time.sleep(3)
                        self.device.input_keyevent("HOME")
                        logger.info(f"设备{self.device_id}:已更换为英语")
                    else:
                        self.element_click(comment="//*[@text='添加语言']/@bounds")
                        time.sleep(3)
                        self.element_click(comment="//*[@text='English']/@bounds")
                        time.sleep(3)
                        self.element_click(comment="//*[@text='United States']/@bounds")
                        time.sleep(3)
                        self.element_click(comment="//*[@text='设为默认']/@bounds")
                else:
                    logger.error(f"设备: {self.device_id}:咱不支持的设备，请手动更换语言为:{self.totle_lang}")
        elif self.totle_lang == "JP":
            self.device.shell("am start -a android.settings.LOCALE_SETTINGS")
            time.sleep(5)
            device_xml = self.get_ui_xml()
            labels = device_xml.xpath('//*[@resource-id="com.android.settings:id/label"]/@content-desc')
            if "日本" in labels[0]:
                logger.info(f"设备{self.device_id}--默认语言为日文，无需更换")
                self.device.input_keyevent("HOME")
                self.lang = self.totle_lang
                return True
            elif "Japanese" in str(labels) or "日本" in str(labels):
                logger.info(f"设备{self.device_id}--默认语言列表有日文,无需添加")
                if "SM-G955F" in self.device_name:
                    logger.error(f"设备: {self.device_id}:暂不支持的设备，请手动更换语言为:{self.totle_lang}")
                    self.device.input_keyevent("HOME")
                    return False
                elif "SM-G950U" in self.device_name:
                    label_aixs = device_xml.xpath(
                        '//*[@resource-id="com.android.settings:id/label"]/@bounds')
                    for i in range(len(labels)):
                        if "Japanese" in labels[i] or "日本" in labels[i]:
                            aixs = self.median_value_pro(label_aixs[i])
                            self.device.input_swipe(start_x=969, start_y=aixs[1], end_x=963, end_y=388, duration=500)
                            time.sleep(3)
                            self.element_click(comment="//*[@text='应用']/@bounds", type=False)
                            self.element_click(comment="//*[@text='Apply']/@bounds", type=False)
                            logger.info(f"设备: {self.device_id}:已更换语言为:日语")
                            time.sleep(3)
                            self.device.input_keyevent("HOME")
                            return True
                else:
                    logger.error(f"设备: {self.device_id}:暂不支持的设备，请手动更换语言为:{self.totle_lang}")
                    self.device.input_keyevent("HOME")
                    return False
            else:
                logger.info(f"设备{self.device_id}--默认语言列表无日文,需添加")
                if "SM-G955F" in self.device_name:
                    pass
                elif "SM-G950U" in self.device_name:
                    self.element_click(comment="//*[@resource-id='com.android.settings:id/add_language']/@bounds")
                    time.sleep(3)
                    try:
                        self.element_click(comment="//*[@text='日本語']/@bounds")
                    except Exception as e:
                        logger.warning(e)
                        self.device.input_swipe(start_x=969, start_y=1400, end_x=963, end_y=188, duration=300)
                        time.sleep(3)
                        self.element_click(comment="//*[@text='日本語']/@bounds")
                    time.sleep(3)
                    self.element_click(comment="//*[@text='Set as default']/@bounds", type=False)
                    self.element_click(comment="//*[@text='设为默认']/@bounds", type=False)
                    time.sleep(3)
                    logger.info(f"设备: {self.device_id}:已更换语言为:日语")
                    self.lang = self.totle_lang
                    return True
                else:
                    logger.error(f"设备: {self.device_id}:暂不支持的设备，请手动更换语言为:{self.totle_lang}")
                    return False

    def add_language(self):
        """
        动作 添加语言
        :return:
        """
        if self.totle_lang == "EN":
            if "CN" in self.lang:
                self.element_click(comment="//*[@text='添加语言']/@bounds")
                time.sleep(3)
                self.element_click(comment="//*[@text='English']/@bounds")
                time.sleep(3)
                self.element_click(comment="//*[@text='United States']/@bounds")
                time.sleep(3)
                self.element_click("//*[@text='编辑']/@bounds")
                time.sleep(3)
                self.device.input_swipe(start_x=969, start_y=724, end_x=963, end_y=388, duration=500)
                time.sleep(3)
                self.device.input_keyevent("BACK")
                time.sleep(3)
                self.device.input_keyevent("HOME")
                logger.info(f"设备{self.device_id}:已更换为英语")
        elif self.totle_lang == "CN":
            pass
        elif self.totle_lang == "JP":
            pass
        else:
            logger.info(f"设备{self.device_id}:暂不支持的语言")

    def is_edit_exist(self):
        if self.element_is_exist(comment="//*[@text='编辑']/@bounds", times=2, type=False):
            return False
        else:
            return True

    def change_eage(self):
        """
        设置默认浏览器为谷歌浏览器
        :return:
        """
        if "CN" in self.lang or "zh" in self.lang:
            self.device.shell('am start -a android.settings.MANAGE_DEFAULT_APPS_SETTINGS')
            device_xml = self.get_ui_xml()
            settings = device_xml.xpath("//*[@text='浏览器应用程序']/@bounds")
            if settings:
                settings_pixel = self.median_value(settings)
                logger.info(f"设备{self.device_id}--找到更换浏览器选项，正在更换浏览器")
                self.device.shell(f"input tap {settings_pixel}")
                device_xml = self.get_ui_xml()
                chrome = device_xml.xpath("//*[@text='Chrome']/@bounds")
                if chrome:
                    chrome_pixel = self.median_value(chrome)
                    self.device.shell(f"input tap {chrome_pixel}")
                else:
                    logger.info(f"设备{self.device_id}--未找到chrome浏览器，请手动处理（任意键继续）")
            else:
                logger.info(f"设备{self.device_id}--未找到更换浏览器选项，可能是语言或设备型号不一致的原因")
            logger.info(f"设备{self.device_id}--更换浏览器完成")
        elif "en" in self.lang or "EN" in self.lang:
            self.device.shell('am start -a android.settings.MANAGE_DEFAULT_APPS_SETTINGS')
            device_xml = self.get_ui_xml()
            settings = device_xml.xpath("//*[@text='Browser app']/@bounds")
            if settings:
                settings_pixel = self.median_value(settings)
                logger.info(f"设备{self.device_id}--找到更换浏览器选项，正在更换浏览器")
                self.device.shell(f"input tap {settings_pixel}")
                device_xml = self.get_ui_xml()
                chrome = device_xml.xpath("//*[@text='Chrome']/@bounds")
                if chrome:
                    chrome_pixel = self.median_value(chrome)
                    self.device.shell(f"input tap {chrome_pixel}")
                else:
                    logger.error(f"设备{self.device_id}--未找到chrome浏览器，请手动处理")
            else:
                logger.error(f"设备{self.device_id}--未找到更换浏览器选项，可能是由于设备不支持的原因")
            logger.info(f"设备{self.device_id}--更换浏览器完成")
        elif "JP" in self.lang or "jp" in self.lang:
            self.device.shell('am start -a android.settings.MANAGE_DEFAULT_APPS_SETTINGS')
            if self.element_is_exist(comment="//*[@text='ブラウザアプリ']/@bounds"):
                self.element_click("//*[@text='ブラウザアプリ']/@bounds")
                logger.info(f"设备{self.device_id}--找到更换浏览器选项，正在更换浏览器")
                device_xml = self.get_ui_xml()
                chrome = device_xml.xpath("//*[@text='Chrome']/@bounds")
                if chrome:
                    self.element_click("//*[@text='Chrome']/@bounds")
                else:
                    logger.error(f"设备{self.device_id}--未找到chrome浏览器，请手动处理")
            else:
                logger.error(f"设备{self.device_id}--未找到更换浏览器选项，可能是由于设备不支持的原因")
            logger.info(f"设备{self.device_id}--更换浏览器完成")

    def median_value_pro(self, number):
        if type(number) == list:
            number = number[0]
        number = eval(str(number).replace("][", "],["))
        real_aixs = [number[0][0] / 2 + number[1][0] / 2, number[0][1] / 2 + number[1][1] / 2]
        return real_aixs

    def median_value_old(self, numer):
        """
        取元素矩阵中间坐标点
        :param num:
        :return:
        """
        li_list = []
        index_subscript = numer[-1].replace("[", '').replace("]", ' ')
        index_list = index_subscript.split(' ')
        index_1 = index_list[0].split(",")
        index_2 = index_list[1].split(",")
        subscript_x = (int(index_1[0]) + int(index_2[0])) / 2
        subscript_y = (int(index_1[1]) + int(index_2[1])) / 2
        li_list.append(subscript_x)
        li_list.append(subscript_y)
        return li_list

    def element_click(self, comment, type=True):
        """
        根据元素点击
        :param device:
        :param comment:
        :return:
        """
        if type == True:
            for i in range(3):
                xpath_html = self.get_ui_xml()
                add_profile = xpath_html.xpath(comment)
                if add_profile == None:
                    time.sleep(3)
                    logger.info("没有找到元素:" + comment + "----重试" + str(i))
                else:
                    break
            add_profile_point = self.median_value_pro(add_profile)
            self.device.input_tap(add_profile_point[0], add_profile_point[1])
        elif type == False:
            try:
                for i in range(3):
                    xpath_html = self.get_ui_xml()
                    add_profile = xpath_html.xpath(comment)
                    if add_profile == None:
                        time.sleep(3)
                        logger.info("没有找到元素:" + comment + "----重试" + str(i))
                    else:
                        break
                add_profile_point = self.median_value_pro(add_profile)
                self.device.input_tap(add_profile_point[0], add_profile_point[1])
                return True
            except:
                logger.warning("没有找到元素:" + comment)

    def element_is_exist(self, comment, times=1, sleeper=3, type=True):
        """
        判断元素是否存在
        :param comment:
        :param type:
        :return:
        """
        if type == True:
            for i in range(times):
                xpath_html = self.get_ui_xml()
                add_profile = xpath_html.xpath(comment)
                if add_profile == None:
                    time.sleep(sleeper)
                    logger.info("没有找到元素:" + comment + "----重试" + str(i))
            return True
        elif type == False:
            try:
                for i in range(times):
                    xpath_html = self.get_ui_xml()
                    add_profile = xpath_html.xpath(comment)
                    if add_profile == None:
                        time.sleep(sleeper)
                        logger.info("没有找到元素:" + comment + "----重试" + str(i))
                return True
            except:
                logger.warning("没有找到元素:" + comment)
                return False

    def clear_cache(self):
        """
        关闭清除openvpn缓存
        :param device:
        :return:
        """
        self.device.shell("input keyevent KEYCODE_WAKEUP")
        self.device.shell('input keyevent 187')
        try:
            self.element_click(comment="//*[@resource-id='com.sec.android.app.launcher:id/clear_all_button']/@bounds", type=False)
        except:
            self.device.shell('input keyevent 187')
        self.device.shell("am force-stop net.openvpn.openvpn")
        self.device.shell("pm clear net.openvpn.openvpn")
        self.device.shell("am force-stop com.android.chrome")
        self.device.shell("pm clear com.android.chrome")

    def change_time_zone(self):
        if "SM-G950U" in self.device_name:
            self.change_time_zone_SM950U()

    def change_time_zone_SM9500(self):
        print(self.device_name)
        pass

    def change_time_zone_SM950U(self):
        self.device.shell("push yadb /data/local/tmp")
        res = self.device.shell("getprop persist.sys.timezone")
        if self.totle_time_zone not in res:
            logger.warning(f"设备{self.device_id}--现时区设置：{res},与所设语言时区设置不一致,正在修改")
            self.device.shell("am start -n com.android.settings/.Settings")
            time.sleep(3)
            self.device.input_swipe(start_x=200, start_y=1500, end_x=200, end_y=300, duration=300)
            time.sleep(3)
            self.element_click(comment="//*[@text='一般管理']/@bounds")
            time.sleep(3)
            self.element_click(comment="//*[@text='日付と時刻']/@bounds")
            time.sleep(3)
            if "1" in self.device.shell("settings get global auto_time"):
                self.element_click(comment="//*[@text='自動日時設定']/@bounds")
            else:
                pass
            time.sleep(3)
            self.element_click(comment="//*[@text='タイムゾーンを選択']/@bounds")
            time.sleep(3)
            self.element_click(comment="//*[@text='地域']/@bounds")
            time.sleep(3)
            while True:
                try:
                    self.element_click("//*[@text='日本']/@bounds", type=True)
                    break
                except Exception as e:
                    self.device.input_swipe(start_x=600, start_y=1500, end_x=600, end_y=300, duration=200)
                time.sleep(0.5)
            self.device.input_keyevent("BACK")
            time.sleep(3)
            self.element_click(comment="//*[@text='自動日時設定']/@bounds")
            time.sleep(3)
            self.device.input_keyevent("HOME")
            return True
        elif self.totle_time_zone == None:
            logger.error(f"设备{self.device_id}--暂未支持更换该时区")
            return False
        elif self.totle_time_zone in res:
            logger.info(f"设备{self.device_id}--现在时区为{res},目标时区为{self.totle_time_zone},无需更换")

    def send_text(self, text):
        """
        通过yadb输入文字
        :param text:
        :return:
        """
        # res = self.device.shell(f"rm /sdcard/window_clipboard")
        # print(res)
        # self.device.shell("app_process -Djava.class.path=/data/local/tmp/yadb /data/local/tmp com.ysbing.yadb.Main -keyboard 日本")
        pass

    def set_chrome(self):
        pass

    def change_vpn(self, data):
        """
        切换ip主程序，支持版本 324,342
        :param device: str，设备wifi连接地址
        :param data: json，vpn相关参数
        :return:
        """
        for i in range(3):
            try:
                self.device.shell("am force-stop net.openvpn.openvpn")
                self.device.shell("pm clear net.openvpn.openvpn")
            except:
                pass
            time.sleep(1)
        logger.info(f"正在清空设备-{self.device_id}- 的vpn缓存,可能出现断链,需等待约10秒")
        time.sleep(11)
        if self.settings["openvpn"] == "openvpn342":  # 支持版本342
            logger.info(f"设备{self.device_id}: 设备vpn安装版本为342，采用链接方式链接")
            time.sleep(2)
            self.device.shell("am start -n net.openvpn.openvpn/net.openvpn.unified.MainActivity t28")
            time.sleep(5)
            self.element_click(comment="//*[@text='AGREE']/@bounds")  # 点击同意
            time.sleep(3)
            self.device.input_text(data["vpn_url"])  # 输入vpn链接地址
            time.sleep(3)
            self.element_click(comment="//*[@text='NEXT']/@bounds")  # 点击NEXT
            time.sleep(3)
            self.element_click(comment="//*[@text='ACCEPT']/@bounds")  # 点击ACCEPT
            time.sleep(8)
            self.device.input_text(data["vpn_acc"])  # 输入vpn账号
            time.sleep(3)
            self.element_click(comment="//*[@text='Password']/@bounds")  # 点击密码输入框
            time.sleep(3)
            self.device.input_text(data["vpn_pwd"])  # 输入vpn密码
            time.sleep(3)
            # try:
            #     self.element_click(comment="//*[@text='Connect after import']/@*")  # 点击勾选框
            # except:
            #     self.device.shell("input keyevent BACK")
            #     self.element_click(comment="//*[@text='Connect after import']/@*")  # 点击勾选框
            try:
                self.element_click(comment="//*[@text='IMPORT']/@bounds")  # 点击导入（IMPORT）
            except:
                self.device.shell("input keyevent BACK")
                self.element_click(comment="//*[@text='IMPORT']/@bounds")  # 点击导入（IMPORT）
            time.sleep(5)
            self.element_click(comment="//*[@resource-id='Edit Profile']/@bounds")  # 输入vpn密码
            time.sleep(3)
            self.device.input_swipe(start_x=597, start_y=768, end_x=597, end_y=400, duration=300)
            time.sleep(3)
            self.element_click(comment="//*[@resource-id='Enable checkbox Save password']/@bounds")  # 点击SAVE PASSWORD
            time.sleep(5)
            self.element_click(comment="//*//*[@text='Password']/@bounds")  # 点击password框
            time.sleep(2)
            self.device.input_text(data["vpn_pwd"])
            time.sleep(3)
            self.element_click(comment="//*[@resource-id='save']/@bounds")  # 点击 SAVE
            time.sleep(3)
            self.element_click(comment="//*[@resource-id='Connection Toggle']/@bounds")
            time.sleep(3)
            self.element_click(comment="//*[@text='OK']/@bounds", type=False)
            # self.device.input_keyevent(3)  # 返回手机主页（home）

        # if self.settings["openvpn"] == "openvpn342":  # 支持版本342
        #     logger.info(f"设备{self.device_id}: 设备vpn安装版本为342，也采用file文件方式连接")
        #     time.sleep(2)
        #     self.device.shell("am start -n net.openvpn.openvpn/net.openvpn.unified.MainActivity t28")
        #     time.sleep(5)
        #     self.element_click(comment="//*[@text='AGREE']/@*")  # 点击同意
        #     time.sleep(3)
        #     self.device.input_text(data["vpn_url"])  # 输入vpn链接地址
        #     time.sleep(3)
        #     self.element_click(comment="//*[@text='NEXT']/@*")  # 点击NEXT
        #     time.sleep(3)
        #     self.device.input_tap(852, 1952)  # 点击ACCEPT
        #     time.sleep(5)
        #     self.element_click(comment="//*[@text='Upload File']/@*")  # 点击密码输入框
        #     time.sleep(3)
        #     self.element_click(comment="//*[@text='BROWSE']/@*")  # 点击勾选框
        #     time.sleep(3)
        #     self.element_click(comment="//*[@text='IMPORT']/@*")  # 点击导入（IMPORT）
        #     time.sleep(5)
        #     self.device.input_text(data["vpn_pwd"])  # 输入vpn密码
        #     time.sleep(3)
        #     self.element_click(comment="//*[@text='OK']/@*")  # 点击OK
        #     time.sleep(5)
        #     self.device.input_tap(758, 1901)
        #     self.device.input_keyevent(3)  # 返回手机主页（home）
        elif self.settings["openvpn"] == "openvpn324":  # 支持版本324
            logger.info(f"设备{self.device_id}: 设备vpn安装版本为324,采用导入文件形式连接")
            logger.info(f"设备{self.device_id}: 查找设备是否有本地文件, vpn账号:{data['vpn_acc']}")
            ovpn = self.ovpnfile_is_exists(data)
            if ovpn:
                logger.info(f"设备{self.device_id}: 有本地文件ovpn文件, vpn账号:{data['vpn_acc']}")
                self.device.push(os.path.join(os.getcwd(), ovpn["path"]), f'/storage/emulated/0/{ovpn["file_name"]}')
                logger.info(f"设备{self.device_id}:vpn文件导入成功:{ovpn['file_name']}")
                time.sleep(2)
            else:
                logger.info(
                    f"设备{self.device_id}: 本地没有ovpn文件, vpn账号:{data['vpn_acc']},准备下载专属file文件")
                time.sleep(3)
                logger.info(f"设备{self.device_id}: 正在下载专属file文件")
                get_vpn_profile(self.data)
                logger.info(f"设备{self.device_id}: 专属file文件下载完毕")
                time.sleep(2)
                ovpn = self.ovpnfile_is_exists(data)
                if ovpn:
                    self.device.push(os.path.join(os.getcwd(), ovpn["path"]),
                                     f'/storage/emulated/0/{ovpn["file_name"]}')
                    logger.info(f"设备{self.device_id}:vpn文件导入成功:{ovpn['file_name']}")
                else:
                    logger.info(f"设备{self.device_id}:vpn文件下载失败")
            self.device.shell("am start -n net.openvpn.openvpn/net.openvpn.unified.MainActivity t28")
            self.element_click(comment="//*[@text='AGREE']/@bounds", type=False)  # 点击同意
            time.sleep(3)
            self.element_click(comment="//*[@text='FILE']/@bounds")
            time.sleep(3)
            self.element_click(comment="//*[@text='ALLOW']/@bounds", type=False)
            time.sleep(3)
            self.element_click(comment="//*[@text='ALWAYS ALLOW']/@bounds", type=False)
            time.sleep(3)
            self.element_click(comment=f"//*[@text='{ovpn['file_name']}']/@bounds", type=True)
            time.sleep(3)
            self.element_click(comment="//*[@text='']/@bounds", type=False)
        else:
            logger.error(f"设备{self.device_id}: 不支持的open版本")

    def ovpnfile_is_exists(self, data):
        url = data["vpn_url"]
        file_name = f"{url.replace('.', '-').replace(':', '-')}-{data['vpn_acc']}.ovpn"
        path = f".\openvpn\\{file_name}"
        if os.path.exists(path=path):
            ovpn = {
                "file_name": file_name,
                "path": path[2:]
            }
            return ovpn
        else:
            return False

    def screen_wake(self):
        """
        唤醒设备
        """
        self.device.shell('input keyevent KEYCODE_WAKEUP')

    def is_screen_active(self):
        """
        判断屏幕是否亮屏, 息屏返回False, 亮屏返回True
        """
        res = self.device.shell("dumpsys power | findstr mScreenOnFully")
        return "true" in res

    def eage_ready(self):
        """
        处理chrome浏览器初始弹窗
        :return:
        """
        if "chrome116" in self.settings["chrome"]:
            logger.info(f"设备{self.device_id}: 开始处理浏览器初始弹窗,浏览器版本116")
            if self.is_screen_active() == False:
                self.screen_wake()
                time.sleep(2)
            self.device.shell("am start -n org.chromium.chrome/.browser.ChromeTabbedActivity")
            time.sleep(5)
            self.element_click(comment="//*[@text='ALLOW']/@bounds", type=False)
            time.sleep(2)
            self.element_click(comment="//*[@text='ALLOW']/@bounds", type=False)
            time.sleep(2)
            self.element_click(comment="//*[@text='Accept & continue']/@bounds", type=False)
            time.sleep(2)
            self.element_click(comment="//*[@text='Next']/@bounds", type=False)
            time.sleep(2)
            self.element_click(comment="//*[@text='No Thanks']/@bounds", type=False)
            time.sleep(2)
            self.element_click(comment="//*[@text='ALWAYS ALLOW']/@bounds", type=False)
            time.sleep(2)
            self.element_click(comment="//*[@text='ALWAYS ALLOW']/@bounds", type=False)
            if self.element_is_exist(comment="//*[@text='UPDATA']/@bounds", type=False) == True:
                logger.info(f"设备{self.device_id}: 发现UPDATE")
                self.device.shell("input keyevent KEYCODE_BACK")
                time.sleep(2)
            self.element_click(comment="//*[@text='Next']/@bounds", type=False)
            self.element_click(comment="//*[@text='No Thanks']/@bounds", type=False)
            logger.info(f"设备{self.device_id}: 浏览器初始弹窗处理完成")
            return True
        elif "chrome125" in self.settings["chrome"]:
            logger.info(f"设备{self.device_id}: 开始处理浏览器初始弹窗,浏览器版本125")
            if self.is_screen_active() == False:
                self.screen_wake()
                time.sleep(2)
            self.device.shell("am start -n com.android.chrome/com.google.android.apps.chrome.Main")
            time.sleep(2)
            if self.element_is_exist(comment="//*[@text='UPDATA']/@bounds", type=False) == True:
                logger.info(f"设备{self.device_id}: 发现UPDATE")
                self.device.shell("input keyevent KEYCODE_BACK")
                time.sleep(2)
            self.element_click(comment="//*[@text='Continue']/@bounds", type=False)
            time.sleep(2)
            self.element_click(comment="//*[@text='Use without an account']/@bounds", type=False)
            time.sleep(2)
            self.device.input_swipe(start_x=489, start_y=1503, end_x=489, end_y=1134, duration=500)
            time.sleep(2)
            self.element_click(comment="//*[@text='Got it']/@bounds", type=False)
            time.sleep(2)
            self.element_click(comment="//*[@text='Keep Google']/@bounds", type=False)

    def get_top_activity(self):
        """
        获取当前顶层的Activity
        :return:
        """
        result = self.device.shell("dumpsys activity top | grep ACTIVITY | tail -n 1").strip()
        return result.strip()

    def main(self):
        # try:
        self.software_version_ctrl()
        self.clear_cache()
        print(self.lang)
        self.change_font()
        self.change_eage()
        self.change_vpn(self.data)
        logger.info(f"设备{self.device_id}--全部设置完毕，可执行下一步任务")
        return True
        # except Exception as e:
        #     print(e)
        #     logger.error("运行错误")
        #     return False

    def get_device_language(self):
        self.lang = self.device.shell("getprop persist.sys.locale")
        return self.lang

    def test(self):
        res = self.change_font()
        time.sleep(3)
        self.change_time_zone()


if __name__ == '__main__':
    data = {"vpn_url": "107.149.212.58:943", "vpn_acc": "zhang002", "vpn_pwd": "888555222"}
    auto_ins = AutoInstall(device_id="192.168.0.23:5555", data=data)
    auto_ins.screen_wake()
    auto_ins.eage_ready()