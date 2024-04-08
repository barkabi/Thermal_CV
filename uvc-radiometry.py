#!/usr/bin/env python
# -*- coding: utf-8 -*-

from uvctypes import *
import time
import cv2
import numpy as np
try:
  from queue import Queue
except ImportError:
  from Queue import Queue
import platform
import time
import busio
import board
import adafruit_amg88xx
import os
BUF_SIZE = 2
q = Queue(BUF_SIZE)

def py_frame_callback(frame, userptr):

  array_pointer = cast(frame.contents.data, POINTER(c_uint16 * (frame.contents.width * frame.contents.height)))
  data = np.frombuffer(
    array_pointer.contents, dtype=np.dtype(np.uint16)
  ).reshape(
    frame.contents.height, frame.contents.width
  ) # no copy

  # data = np.fromiter(
  #   frame.contents.data, dtype=np.dtype(np.uint8), count=frame.contents.data_bytes
  # ).reshape(
  #   frame.contents.height, frame.contents.width, 2
  # ) # copy

  if frame.contents.data_bytes != (2 * frame.contents.width * frame.contents.height):
    return

  if not q.full():
    q.put(data)

PTR_PY_FRAME_CALLBACK = CFUNCTYPE(None, POINTER(uvc_frame), c_void_p)(py_frame_callback)

def ktof(val):
  return (1.8 * ktoc(val) + 32.0)

def ktoc(val):
  return (val - 27315) / 100.0

def raw_to_8bit(data):
  cv2.normalize(data, data, 0, 65535, cv2.NORM_MINMAX)
  np.right_shift(data, 8, data)
  return np.uint8(data)

def display_temperature(img, val_k, loc, color):
  val = ktof(val_k)
  cv2.putText(img,"{0:.1f} degF".format(val), loc, cv2.FONT_HERSHEY_SIMPLEX, 0.75, color, 2)
  x, y = loc
  cv2.line(img, (x - 2, y), (x + 2, y), color, 1)
  cv2.line(img, (x, y - 2), (x, y + 2), color, 1)
  
def save_pairs(paired_data,directory, counter):
  
  if not os.path.exists(directory):
    os.makedirs(directory)
    
  #Save each pair of matrices
  matrix_Flir, matrix_AMG=paired_data
  np.savez(f'{directory}/pair{counter}.npz',matrix_Flir,matrix_AMG) 

def main():
  ctx = POINTER(uvc_context)()
  dev = POINTER(uvc_device)()
  devh = POINTER(uvc_device_handle)()
  ctrl = uvc_stream_ctrl()

  res = libuvc.uvc_init(byref(ctx), 0)
  
  #Initialization for AMG8833
  i2c = busio.I2C(board.SCL, board.SDA)
  amg = adafruit_amg88xx.AMG88XX(i2c)
  counter=0
  if res < 0:
    print("uvc_init error")
    exit(1)

  try:
    res = libuvc.uvc_find_device(ctx, byref(dev), PT_USB_VID, PT_USB_PID, 0)
    if res < 0:
      print("uvc_find_device error")
      exit(1)

    try:
      res = libuvc.uvc_open(dev, byref(devh))
      if res < 0:
        print("uvc_open error")
        exit(1)

      print("device opened!")

      print_device_info(devh)
      print_device_formats(devh)

      frame_formats = uvc_get_frame_formats_by_guid(devh, VS_FMT_GUID_Y16)
      if len(frame_formats) == 0:
        print("device does not support Y16")
        exit(1)

      libuvc.uvc_get_stream_ctrl_format_size(devh, byref(ctrl), UVC_FRAME_FORMAT_Y16,
        frame_formats[0].wWidth, frame_formats[0].wHeight, int(1e7 / frame_formats[0].dwDefaultFrameInterval)
      )

      res = libuvc.uvc_start_streaming(devh, byref(ctrl), PTR_PY_FRAME_CALLBACK, None, 0)
      if res < 0:
        print("uvc_start_streaming failed: {0}".format(res))
        exit(1)

      try:
        while True:
          data = q.get(True, 500)
          AMG_Numpy=np.array(amg.pixels)
          Flir_Numpy=np.array(data)
          print(type(data),type(amg.pixels))
          print("AMG ",AMG_Numpy.shape)
          #print(Flir_Numpy)
          #for row in amg.pixels:
          #    # Pad to 1 decimal place
          #    print(["{0:.1f}".format(temp) for temp in row])
          #    print("")
          #print("\n")
          
          if data is None:
            break
          data = cv2.resize(data[:,:], (120, 160))

          minVal, maxVal, minLoc, maxLoc = cv2.minMaxLoc(data)

          img = raw_to_8bit(data)
          #Convert fahrenheit to celcius
          Flir_celcius_array=np.round((img-32)*(5/9), decimals=1)
          print("Flir ",Flir_celcius_array.shape,img.shape)
          save_pairs([AMG_Numpy,Flir_celcius_array],"paired_images", counter)
          counter+=1
          #display_temperature(img, minVal, minLoc, (255, 0, 0))
          #display_temperature(img, maxVal, maxLoc, (0, 0, 255))
          #cv2.imshow('Lepton Radiometry', celcius_array)
          #cv2.waitKey(1)

        cv2.destroyAllWindows()
      finally:
        libuvc.uvc_stop_streaming(devh)

      print("done")
    finally:
      libuvc.uvc_unref_device(dev)
  finally:
    libuvc.uvc_exit(ctx)

if __name__ == '__main__':
  main()
