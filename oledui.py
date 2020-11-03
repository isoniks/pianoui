#!/usr/bin/python

from __future__ import unicode_literals

"""
Volumio OLED User Interface
Designed for ssd1322 OLED 256x64 x Volumio 2 x RPi
Inspired by diehardsk/Volumio-OledUI
"""

import requests
import os
import sys
import json

from time import time, sleep
from threading import Thread
from socketIO_client import SocketIO

# Imports for OLED display
from luma.core.interface.serial import spi
from luma.oled.device import ssd1322
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

from modules.display import *

volumio_host = 'localhost'
volumio_port = 3000

volumioIO = SocketIO(volumio_host, volumio_port)

STATE_NONE = -1
STATE_PLAYER = 0
STATE_VOLUME = 3

UPDATE_INTERVAL = 0.034
PIXEL_SHIFT_TIME = 120    #time between picture position shifts in sec.

interface = spi(device=0, port=0)
oled = ssd1322(interface)

oled.WIDTH = 256
oled.HEIGHT = 64
oled.state = STATE_NONE
oled.stateTimeout = 0
oled.timeOutRunning = False
oled.activeSong = ''
oled.activeArtist = 'VOLuMIO'
oled.playState = 'unknown'
oled.playPosition = 0
oled.modal = False
oled.playlistoptions = []
oled.queue = []
oled.libraryFull = []
oled.libraryNames = []
oled.volumeControlDisabled = False
oled.volume = 100

emit_volume = False
emit_track = False

image = Image.new('RGB', (oled.WIDTH + 4, oled.HEIGHT + 4))  #enlarged for pixelshift
oled.clear()

font = load_font('Roboto-Regular.ttf', 24)
font2 = load_font('PixelOperator.ttf', 15)
hugefontaw = load_font('fa-solid-900.ttf', oled.HEIGHT - 4)


def display_update_service():
    pixshift = [2, 2]
    lastshift = prevTime = time()
    while UPDATE_INTERVAL > 0:
        dt = time() - prevTime
        prevTime = time()
        if prevTime-lastshift > PIXEL_SHIFT_TIME: #it's time for pixel shift
            lastshift = prevTime
            if pixshift[0] == 4 and pixshift[1] < 4:
                pixshift[1] += 1
            elif pixshift[1] == 0 and pixshift[0] < 4:
                pixshift[0] += 1
            elif pixshift[0] == 0 and pixshift[1] > 0:
                pixshift[1] -= 1
            else:
                pixshift[0] -= 1
        # auto return to home display screen (from volume display / queue list..)
        if oled.stateTimeout > 0:
            oled.timeOutRunning = True
            oled.stateTimeout -= dt
        elif oled.stateTimeout <= 0 and oled.timeOutRunning:
            oled.timeOutRunning = False
            oled.stateTimeout = 0
            SetState(STATE_PLAYER)
        image.paste("black", [0, 0, image.size[0], image.size[1]])
        try:
            oled.modal.DrawOn(image)
        except AttributeError:
            print ("render error")
        cimg = image.crop((pixshift[0], pixshift[1], pixshift[0] + oled.WIDTH, pixshift[1] + oled.HEIGHT)) 
        oled.display(cimg)
        sleep(UPDATE_INTERVAL)

def SetState(status):
    oled.state = status
    if oled.state == STATE_PLAYER:
        oled.modal = NowPlayingScreen(oled.HEIGHT, oled.WIDTH, oled.activeArtist, oled.activeSong, font, hugefontaw)
        oled.modal.SetPlayingIcon(oled.playState, 0)

def onPushState(data):
    #print(data)
    if 'title' in data:
        newSong = data['title']
    else:
        newSong = ''
    if newSong is None:
        newSong = ''
        
    if 'artist' in data:
        newArtist = data['artist']
    else:
        newArtist = ''
    if newArtist is None:   #volumio can push NoneType
        newArtist = ''
        
    if 'position' in data:                      # current position in queue
        oled.playPosition = data['position']    # didn't work well with volumio ver. < 2.5
        
    if 'status' in data:
        newStatus = data['status']
        
    if oled.state != STATE_VOLUME:            #get volume on startup and remote control
        try:                                  #it is either number or unicode text
            oled.volume = int(data['volume'])
        except (KeyError, ValueError):
            pass
    
    if 'disableVolumeControl' in data:
        oled.volumeControlDisabled = data['disableVolumeControl']

    print(newSong.encode('ascii', 'ignore'))
    if (newSong != oled.activeSong):    # new song
        oled.activeSong = newSong
        oled.activeArtist = newArtist
        if oled.state == STATE_PLAYER:
            oled.modal.UpdatePlayingInfo(newArtist, newSong)

    if newStatus != oled.playState:
        oled.playState = newStatus
        if oled.state == STATE_PLAYER:
            if oled.playState == 'play':
                iconTime = 35
            else:
                iconTime = 80
            oled.modal.SetPlayingIcon(oled.playState, iconTime)


class NowPlayingScreen():
    def __init__(self, height, width, row1, row2, font, fontaw):
        self.height = height
        self.width = width
        self.font = font
        self.fontaw = fontaw
        self.playingText1 = StaticText(self.height, self.width, row1, font, center=True)
        self.playingText2 = ScrollText(self.height, self.width, row2, font)
        self.icon = {'play':'\uf04b', 'pause':'\uf04c', 'stop':'\uf04d'}
        self.playingIcon = self.icon['play']
        self.iconcountdown = 0
        self.text1Pos = (3, 6)
        self.text2Pos = (3, 37)
        self.alfaimage = Image.new('RGBA', image.size, (0, 0, 0, 0))

    def UpdatePlayingInfo(self, row1, row2):
        self.playingText1 = StaticText(self.height, self.width, row1, font, center=True)
        self.playingText2 = ScrollText(self.height, self.width, row2, font)

    def DrawOn(self, image):
        if self.playingIcon != self.icon['stop']:
            self.playingText1.DrawOn(image, self.text1Pos)
            self.playingText2.DrawOn(image, self.text2Pos)
        if self.iconcountdown > 0:
            compositeimage = Image.composite(self.alfaimage, image.convert('RGBA'), self.alfaimage)
            image.paste(compositeimage.convert('RGB'), (0, 0))
            self.iconcountdown -= 1
            
    def SetPlayingIcon(self, state, time=0):
        if state in self.icon:
            self.playingIcon = self.icon[state]
        self.alfaimage.paste((0, 0, 0, 0), [0, 0, image.size[0], image.size[1]])
        drawalfa = ImageDraw.Draw(self.alfaimage)
        iconwidth, iconheight = drawalfa.textsize(self.playingIcon, font=self.fontaw)
        left = (self.width - iconwidth) / 2
        drawalfa.text((left, 4), self.playingIcon, font=self.fontaw, fill=(255, 255, 255, 96))
        self.iconcountdown = time

show_logo("volumio_logo.ppm", oled)
sleep(2)
SetState(STATE_PLAYER)

updateThread = Thread(target=display_update_service)
updateThread.daemon = True
updateThread.start()

def _receive_thread():
    volumioIO.wait()

receive_thread = Thread(target=_receive_thread)
receive_thread.daemon = True
receive_thread.start()

volumioIO.on('pushState', onPushState)

# get list of Playlists and initial state
volumioIO.emit('listPlaylist')
volumioIO.emit('getState')
volumioIO.emit('getQueue')
#volumioIO.emit('getBrowseSources')
sleep(0.1)
try:
    with open('oledconfig.json', 'r') as f:   #load last playing track number
        config = json.load(f)
except IOError:
    pass
else:
    oled.playPosition = config['track']
    
if oled.playState != 'play':
    volumioIO.emit('play', {'value':oled.playPosition})

while True:
    if emit_volume:
        emit_volume = False
        print("volume: " + str(oled.volume))
        volumioIO.emit('volume', oled.volume)
    if emit_track and oled.stateTimeout < 4.5:
        emit_track = False
        try:
            print('Track selected: ' + str(oled.playPosition+1) + '/' + str(len(oled.queue)) + ' ', oled.queue[oled.playPosition].encode('ascii', 'ignore'))
        except IndexError:
            pass
        volumioIO.emit('play', {'value':oled.playPosition})
    sleep(0.1)
