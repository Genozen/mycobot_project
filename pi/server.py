#!/usr/bin/env python3
# coding:utf-8
"""
TCP-to-serial bridge for myCobot 280 Pi.

Receives raw pymycobot binary protocol bytes over TCP and forwards them
to the robot's serial port. Responses from the MCU are read and sent
back to the TCP client.

Based on: https://github.com/elephantrobotics/pymycobot/blob/main/demo/Server.py
Updated to handle raw binary protocol used by pymycobot >= 3.x / 4.x.

Usage (standalone):
    python3 server.py

Typically managed by systemd via mycobot_server.service.
"""

import socket
import serial
import time
import logging
import logging.handlers
import fcntl
import struct
import traceback

try:
    import RPi.GPIO as GPIO
except ImportError:
    GPIO = None

SERIAL_PORT = "/dev/ttyAMA0"
SERIAL_BAUD = 1000000

has_return = [
    0x01, 0x02, 0x03, 0x04, 0x09, 0x12, 0x14, 0x15, 0x17, 0x1B,
    0x20, 0x23, 0x27, 0x2A, 0x2B, 0x2D, 0x2E, 0x3B, 0x3D,
    0x40, 0x42, 0x43, 0x44, 0x4A, 0x4B, 0x50, 0x51, 0x53,
    0x62, 0x65, 0x69,
    0x82, 0x84, 0x86, 0x88, 0x8A,
    0x90, 0x91, 0x92,
    0xB0,
    0xC0, 0xC3,
    0xD0, 0xD1, 0xD5,
    0xE1, 0xE2, 0xE3, 0xE4, 0xE5, 0xE6,
]


def get_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    fmt = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

    console = logging.StreamHandler()
    console.setFormatter(fmt)

    save = logging.handlers.RotatingFileHandler(
        "server.log", maxBytes=10485760, backupCount=1,
    )
    save.setFormatter(fmt)

    logger.addHandler(save)
    logger.addHandler(console)
    return logger


class MycobotServer:

    def __init__(self, host, port, serial_num=SERIAL_PORT, baud=SERIAL_BAUD):
        if GPIO is not None:
            try:
                GPIO.setwarnings(False)
            except Exception:
                pass

        self.logger = get_logger("AS")
        self.serial_num = serial_num
        self.baud = baud

        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.s.bind((host, port))
        print("Binding succeeded!")
        self.s.listen(1)

        self.mc = serial.Serial(self.serial_num, self.baud, timeout=0.1)
        self.logger.info("Serial port {} opened at {} baud".format(serial_num, baud))
        self.serve_forever()

    def serve_forever(self):
        while True:
            try:
                print("waiting connect!------------------")
                conn, addr = self.s.accept()
                self.logger.info("Client connected from {}".format(addr))

                while True:
                    try:
                        data = conn.recv(1024)
                        command = list(data)

                        if not command:
                            print("close disconnect!")
                            break

                        if not self.mc.isOpen():
                            self.mc.open()

                        self.logger.info("get command: {}".format(
                            [hex(v) for v in command],
                        ))

                        if len(command) > 3 and command[3] == 170:
                            if GPIO:
                                GPIO.setmode(GPIO.BCM if command[4] == 0 else GPIO.BOARD)
                        elif len(command) > 5 and command[3] == 171:
                            if GPIO:
                                GPIO.setup(command[4], GPIO.OUT if command[5] else GPIO.IN)
                        elif len(command) > 5 and command[3] == 172:
                            if GPIO:
                                GPIO.output(command[4], command[5])
                        elif len(command) > 4 and command[3] == 173:
                            if GPIO:
                                res = bytes([GPIO.input(command[4])])
                                conn.sendall(res)
                                continue

                        self.write(command)

                        if len(command) > 3 and command[3] in has_return:
                            res = self.read(command)
                            self.logger.info("return datas: {}".format(
                                [hex(v) for v in res],
                            ))
                            conn.sendall(res)

                    except Exception:
                        self.logger.error(traceback.format_exc())
                        try:
                            conn.sendall(str.encode(traceback.format_exc()))
                        except Exception:
                            pass
                        break

            except Exception:
                self.logger.error(traceback.format_exc())
                try:
                    conn.close()
                except Exception:
                    pass
                self.mc.close()

    def write(self, command):
        self.mc.write(command)
        self.mc.flush()

    def read(self, command):
        datas = b""
        data_len = -1
        k = 0
        pre = 0
        t = time.time()
        wait_time = 0.1

        while time.time() - t < wait_time:
            data = self.mc.read()
            k += 1

            if data_len == 1 and data == b"\xfa":
                datas += data
                if [i for i in datas] == command:
                    datas = b""
                    data_len = -1
                    k = 0
                    pre = 0
                    continue
                break
            elif len(datas) == 2:
                data_len = struct.unpack("b", data)[0]
                datas += data
            elif len(datas) > 2 and data_len > 0:
                datas += data
                data_len -= 1
            elif data == b"\xfe":
                if datas == b"":
                    datas += data
                    pre = k
                else:
                    if k - 1 == pre:
                        datas += data
                    else:
                        datas = b"\xfe"
                        pre = k
            else:
                datas = b""

        return datas


if __name__ == "__main__":
    ifname = "wlan0"
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    HOST = socket.inet_ntoa(
        fcntl.ioctl(
            s.fileno(),
            0x8915,
            struct.pack("256s", bytes(ifname, encoding="utf8")),
        )[20:24]
    )
    PORT = 9000
    print("ip: {} port: {}".format(HOST, PORT))
    MycobotServer(HOST, PORT, SERIAL_PORT, SERIAL_BAUD)
