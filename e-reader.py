from pdf2image import convert_from_path
import sys
import os
libdir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'lib')
if os.path.exists(libdir):
    sys.path.append(libdir)
from waveshare_epd import epd5in65f
import logging
import time
import RPi.GPIO as GPIO
from PIL import Image
import tempfile

logging.basicConfig(level=logging.DEBUG)
page_number = 0

def init_images():
    with tempfile.TemporaryDirectory() as path:
        images = convert_from_path(
            '/home/pi/Projects/e-reader/pdf/rpi.pdf',
            dpi=600,
            output_folder=path
        )
    panel_size = (600, 448)
    PALETTE = [
        255, 255, 255,  # white
        0, 255, 0,      # green
        0, 0, 255,      # blue
        255, 0, 0,      # red
        255, 255, 0,    # yellow
        255, 128, 0     # orange
    ] + [0, ] * 250 * 3

    pimage = Image.new("P", (1, 1), 0)
    pimage.putpalette(PALETTE)

    for page_num in range(len(images)):
        logging.info("Rendering page %d:" %page_num)
        images[page_num] = images[page_num].rotate(90, expand=1).resize(panel_size, resample=Image.BICUBIC).convert('RGB', dither=Image.FLOYDSTEINBERG).quantize(palette=pimage)
    
    return images

def display_page(img):
    try:
        logging.info("e-Readerr chage page")
        epd = epd5in65f.EPD()
        logging.info("init and Clear")
        epd.init()
        epd.Clear()
        logging.info("Display bpm image")
        epd.display(epd.getbuffer(img))
        epd.sleep()
        epd.Dev_exit()

    except IOError as e:
        logging.info(e)

    except KeyboardInterrupt:
        logging.info("ctrl + c:")
        epd5in65f.epdconfig.module_exit()
        exit()

def listen_ui():
    home_button = 21
    next_button = 20
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(home_button, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(next_button, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    home_state = GPIO.input(home_button)
    while home_state:
        next_button_state = GPIO.input(next_button)
        if next_button_state == 0:
            GPIO.cleanup()
            return 1
        time.sleep(0.25)
        home_state = GPIO.input(home_button)

    GPIO.cleanup()
    return 0

images = init_images()
display_page(images[page_number])
run = True

while run:
    current_state = listen_ui()
    if current_state == 1:
        if page_number + 1 < len(images):
            page_number += 1
        display_page(images[page_number])
    else:
        run = False
