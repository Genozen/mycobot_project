"""
Lightweight MJPEG HTTP server for the myCobot 280 Pi camera.
Streams /dev/video0 as MJPEG over HTTP on port 8080.

Usage:
    python3 camera_stream.py
    python3 camera_stream.py --port 8080 --device 0 --width 640 --height 480
"""

import argparse
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler

import cv2


class MJPEGStreamHandler(BaseHTTPRequestHandler):
    camera = None
    lock = threading.Lock()

    def do_GET(self):
        if self.path == '/' or self.path == '/?action=stream':
            self.send_response(200)
            self.send_header('Content-Type',
                             'multipart/x-mixed-replace; boundary=frame')
            self.end_headers()
            try:
                while True:
                    with self.lock:
                        ret, frame = self.camera.read()
                    if not ret:
                        continue
                    _, jpeg = cv2.imencode('.jpg', frame,
                                          [cv2.IMWRITE_JPEG_QUALITY, 80])
                    data = jpeg.tobytes()
                    self.wfile.write(b'--frame\r\n')
                    self.wfile.write(b'Content-Type: image/jpeg\r\n')
                    self.wfile.write(f'Content-Length: {len(data)}\r\n'.encode())
                    self.wfile.write(b'\r\n')
                    self.wfile.write(data)
                    self.wfile.write(b'\r\n')
                    self.wfile.flush()
                    time.sleep(0.1)  # ~10 FPS (safe for Pi 2GB over WiFi)
            except (BrokenPipeError, ConnectionResetError):
                pass
        elif self.path == '/?action=snapshot':
            with self.lock:
                ret, frame = self.camera.read()
            if ret:
                _, jpeg = cv2.imencode('.jpg', frame)
                data = jpeg.tobytes()
                self.send_response(200)
                self.send_header('Content-Type', 'image/jpeg')
                self.send_header('Content-Length', str(len(data)))
                self.end_headers()
                self.wfile.write(data)
            else:
                self.send_error(503, 'Camera not available')
        else:
            self.send_error(404)

    def log_message(self, format, *args):
        pass  # suppress per-request logging


def main():
    parser = argparse.ArgumentParser(description='MJPEG Camera Stream Server')
    parser.add_argument('--port', type=int, default=8080)
    parser.add_argument('--device', type=int, default=0)
    parser.add_argument('--width', type=int, default=640)
    parser.add_argument('--height', type=int, default=480)
    args = parser.parse_args()

    cap = cv2.VideoCapture(args.device)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, args.width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, args.height)

    if not cap.isOpened():
        print(f'ERROR: Cannot open camera /dev/video{args.device}')
        return

    MJPEGStreamHandler.camera = cap

    server = HTTPServer(('0.0.0.0', args.port), MJPEGStreamHandler)
    print(f'Camera stream: http://0.0.0.0:{args.port}/?action=stream')
    print(f'Snapshot:      http://0.0.0.0:{args.port}/?action=snapshot')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        cap.release()
        server.server_close()


if __name__ == '__main__':
    main()
