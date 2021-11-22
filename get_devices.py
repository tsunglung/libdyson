import os
import sys
import platform
import pathlib
import shutil
from getpass import getpass
from typing import Optional
import requests
import certifi
import urllib3

from libdyson.cloud import DysonAccount
from libdyson.cloud.account import DysonAccountCN, DYSON_API_HEADERS
from libdyson.exceptions import (
    DysonAuthRequired,
    DysonInvalidAccountStatus,
    DysonInvalidAuth,
    DysonLoginFailure,
    DysonNetworkError,
    DysonOTPTooFrequently,
    DysonServerError,
)

FILE_PATH = pathlib.Path(__file__).parent.absolute()

class DysonAccountRequest():

    def request(
        self,
        method: str,
        path: str,
        params: Optional[dict] = None,
        data: Optional[dict] = None,
        auth: bool = True,
    ) -> requests.Response:
        """Make API request."""
        if auth and self._auth is None:
            raise DysonAuthRequired
        try:
            response = requests.request(
                method,
                self._HOST + path,
                params=params,
                json=data,
                headers=DYSON_API_HEADERS,
                auth=self._auth if auth else None,
            )
        except requests.RequestException:
            raise DysonNetworkError
        if response.status_code in [401, 403]:
            raise DysonInvalidAuth
        if 500 <= response.status_code < 600:
            raise DysonServerError
        return response


class DysonAccountNew(DysonAccountRequest, DysonAccount):
    pass


class DysonAccountCNNew(DysonAccountRequest, DysonAccountCN):
    pass


def prepare():
    """ prepare """
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    cacert_pem = certifi.where()
    shutil.copyfile(cacert_pem, cacert_pem + ".bak")

    if "Windows" in platform.system():
        DYSON_CERT = f"{FILE_PATH}\libdyson\cloud\certs\DigiCert-chain.crt"
        DYSON_CERT_CN = f"{FILE_PATH}\libdyson\cloud\certs\DigiCert-cn-chain.crt"
    else:
        DYSON_CERT = f"{FILE_PATH}/libdyson/cloud/certs/DigiCert-chain.crt"
        DYSON_CERT_CN = f"{FILE_PATH}/libdyson/cloud/certs/DigiCert-cn-chain.crt"

    with open(DYSON_CERT, "r") as f_in:
        with open(cacert_pem, "a") as f_out:
            f_out.write("\n" + f_in.read())


def get_devices():
    """ Get devices """
    print("Please choose your account region")
    print("1: Mainland China")
    print("2: Rest of the World")
    region = input("Region [1/2]: ")

    if region == "1":
        account = DysonAccountCNNew()
        mobile = input("Phone number: ")
        verify = account.login_mobile_otp(f"+86{mobile}")
        otp = input("Verification code: ")
        verify(otp)
    elif region == "2":
        region = input("Region code: ")
        account = DysonAccountNew()
        email = input("Email: ")
        verify = account.login_email_otp(email, region)
        password = getpass()
        otp = input("Verification code: ")
        verify(otp, password)
    else:
        print(f"Invalid input {region}")
        return

    devices = account.devices()
    for device in devices:
        print()
        print(f"Serial: {device.serial}")
        print(f"Name: {device.name}")
        print(f"Device Type: {device.product_type}")
        print(f"Credential: {device.credential}")

def finish():
    """ Finish """
    cacert_pem = certifi.where()
    os.remove(cacert_pem)
    os.rename(cacert_pem + ".bak", cacert_pem)


def main():
    """ main function """
    if "Windows" not in platform.system() and os.geteuid() != 0:
        print("Please sudo to run this script.")
        sys.exit(1)

    prepare()

    try:
        get_devices()
    except DysonInvalidAuth:
        print('DysonInvalidAuth, Please logout in Dyson Link app if logined, or login if already logout, then try later')
        pass
    except DysonServerError:
        print('DysonServerError, Please try later')
        pass
    except DysonAuthRequired:
        print('Requried Authorization')
        pass
    except DysonNetworkError:
        print('Can not connect to Dyson Network, Please try later')
        pass
    except DysonLoginFailure:
        print('Login infomation is incorrected, Please check the info')
        pass
    except DysonOTPTooFrequently:
        print('OTP too frequently, Please try later')
        pass

    finish()


if __name__ == '__main__':
    main()
