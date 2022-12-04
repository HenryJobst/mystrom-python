import json
import time

import requests
import schedule

from base import session_factory
from models.mystrom_device import MystromDevice
from models.mystrom_result import MystromResult


@schedule.repeat(schedule.every(1).minutes)
def trigger():
    for device in get_active_devices():
        request_data_and_store(device)


def get_active_devices():
    return session.query(MystromDevice).filter(MystromDevice.active).all()


def request_data_and_store(device):
    try:
        response = requests.get(f'http://{device.ip}/report')
    except requests.ConnectionError:
        print(f'Device {device.name} with ip address {device.ip} seems to be '
              f'not reachable.')
        return
    except requests.Timeout:
        print(f'Request to device {device.name} with ip address {device.ip} '
              f'timed out.')
        return
    except requests.RequestException:
        print(f'Request to device {device.name} with ip address {device.ip} '
              f'failed.')
        return

    try:
        response = json.loads(response.text)
    except json.decoder.JSONDecodeError:
        print(f'Request to device {device.name} with ip address {device.ip} '
              f'returns invalid JSON response.')
        return

    mystrom_result = MystromResult(device_id=device.id,
                                   power=response["power"],
                                   ws=response["Ws"],
                                   relay=response["relay"],
                                   temperature=response["temperature"])

    print(mystrom_result.__repr__())
    session.add(mystrom_result, device)
    session.commit()


if __name__ == '__main__':
    session = session_factory()

    while True:
        # Checks whether a scheduled task
        # is pending to run or not
        schedule.run_pending()
        time.sleep(1)
