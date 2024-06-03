import requests
import os


def get_vpn_profile(data):

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                      '(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36 Edg/125.0.0.0',
    }
    session = requests.session()
    session.get(url=f"https://{data['vpn_url']}/", headers=headers, verify=False)
    session.post(url=f"https://{data['vpn_url']}/__auth__", headers=headers,
                 data={"username": data["vpn_acc"], "password": data["vpn_pwd"]}, verify=False)
    # print(login.text)
    # print(session.cookies)
    params = {
        'comment': '',
        'autologin': 'false',
        'tlscryptv2': 'true',
    }
    response = session.get(f'https://{data["vpn_url"]}/create_profile', params=params, headers=headers, verify=False).text
    os.makedirs("./openvpn", exist_ok=True)
    file_name = f"{data['vpn_url'].replace('.', '-').replace(':', '-')}-{data['vpn_acc']}"
    with open(f"./openvpn/{file_name}.ovpn", "w") as f:
        f.write(response)
        f.close()


if __name__ == "__main__":
    data = {
        "vpn_acc": "zhang001",
        "vpn_pwd": "888555222",
        "vpn_url": "107.149.212.58:943"
    }
    get_vpn_profile(data=data)
