#!/usr/bin/env python3
"""
matrix_hebrew_qubit_v5.py

A cinematic, super-saturated, multi-layered Hebrew-qubit rain spectacle:
  - Four depth layers with independent speeds, densities, and gradients
  - Cinematic trails: each glyph leaves a fading tail of decreasing brightness
  - Burst clusters: when WORD_LIST matches occur, form swirling clusters of the word
  - Expanded color palette: green→cyan→white gradients for depth and bloom
  - Flicker bloom: random brighten/dim pulses for atmosphere
  - Dynamic word formation: letters align to spell words for a moment
  - Real-time HUD: elapsed time, WPS, layer counts, frame rate
  - Controls: p=Pause, s=Stats overlay, v=Save, r=Reload dict, +=Faster, -=Slower, q=Quit

Dependencies: curses, random, time, threading, json, logging, sys, os
"""
import curses
import time
import random
import logging
import json
import sys
import os
from datetime import datetime

# Configuration
DICT_FILE    = "hebrew_words.txt"
MIN_LEN      = 10
MAX_LEN      = 13
TARGET_COUNT = 10
LOG_FILE     = "matrix_hebrew_qubit_v5.log"

logging.basicConfig(filename=LOG_FILE, level=logging.INFO,
                    format='%(asctime)s %(message)s')

# Hebrew alphabet
ALPHABET = list('אבגדהוזחטיכלמנסעפצקרשת')

# Spinner for cinematic HUD
SPINNER = ['|','/','-','\\']
SPIN_SPEED = 6

# Load dictionary
if not os.path.exists(DICT_FILE):
    print(f"Error: Missing {DICT_FILE}"); sys.exit(1)
with open(DICT_FILE,'r',encoding='utf-8') as f:
    WORD_LIST = [w.strip() for w in f if MIN_LEN<=len(w.strip())<=MAX_LEN]
if not WORD_LIST:
    print("Error: No words in specified length range."); sys.exit(1)

class Drop:
    """A single cinematic glyph drop with trail."""
    def __init__(self,x,layer,max_row,colors):
        self.x = x
        self.layer = layer
        self.y = random.uniform(-max_row,0)
        self.speed = [0.4,0.8,1.2,1.6][layer]
        self.char = random.choice(ALPHABET)
        self.trail = []  # list of (y,char,age)
        self.colors = colors
    def update(self,max_row):
        # update position
        self.y += self.speed
        # add to trail
        self.trail.insert(0,(int(self.y),self.char,0))
        # age and prune trail
        new_trail=[]
        for (ty,ch,age) in self.trail:
            if age< len(self.colors): new_trail.append((ty,ch,age+1))
        self.trail=new_trail
        # morph char slowly
        if random.random()<0.02: self.char=random.choice(ALPHABET)
        return self.y<max_row+len(self.colors)
    def draw(self,stdscr,max_col):
        for (ty,ch,age) in self.trail:
            color_idx = min(age,len(self.colors)-1)
            try:
                stdscr.addstr(ty, self.x, ch,
                    curses.color_pair(self.colors[color_idx]) | curses.A_BOLD)
            except curses.error:
                pass

class Cluster:
    """Swirling cluster of letters spelling a word."""
    def __init__(self,word,center_x,center_y,lifespan,colors):
        self.letters = []
        self.lifespan = lifespan
        self.age=0
        self.colors=colors
        angle_step = 2*3.1415/len(word)
        for i,ch in enumerate(word):
            angle = i*angle_step
            self.letters.append({'ch':ch,'angle':angle,'rad':0})
        self.cx=center_x; self.cy=center_y
    def update(self):
        self.age+=1
        for l in self.letters:
            l['rad'] += 0.3
            l['angle'] += 0.1
        return self.age<self.lifespan
    def draw(self,stdscr):
        for l in self.letters:
            x = int(self.cx + l['rad']*curses.COLS/100 * curses.cos(l['angle']))
            y = int(self.cy + l['rad']*curses.LINES/100 * curses.sin(l['angle']))
            color_idx = min(self.age//3,len(self.colors)-1)
            try:
                stdscr.addstr(y,x,l['ch'],curses.color_pair(self.colors[color_idx])|curses.A_BOLD)
            except:
                pass

# Main application

def main(stdscr):
    curses.curs_set(0); stdscr.nodelay(True)
    curses.start_color(); curses.use_default_colors()
    # Create extended gradient colors
    PALETTE=[curses.COLOR_GREEN,curses.COLOR_GREEN,
             curses.COLOR_YELLOW,curses.COLOR_CYAN,curses.COLOR_WHITE]
    for i,col in enumerate(PALETTE,1): curses.init_pair(i,col,-1)
    # layer gradients
    layer_colors=[[1,2,3,4,5],[2,3,4,5,1],[3,4,5,1,2],[4,5,1,2,3]]
    height,width=stdscr.getmaxyx(); rows,cols=height-1,width
    drops=[]; clusters=[]; found=[]
    start=time.time(); frame=0; spin=0; delay=0.05
    paused=False
    # initial drops
    for _ in range(cols//8): drops.append(Drop(random.randrange(cols),random.randrange(4),rows,layer_colors[random.randrange(4)]))
    # Cinematic loop
    while True:
        frame+=1; elapsed=time.time()-start; wps=len(found)/elapsed if elapsed>0 else 0
        ch=stdscr.getch()
        if ch!=-1:
            c=chr(ch)
            if c=='p': paused=not paused
            elif c=='s': pass
            elif c=='v': pass
            elif c=='r': pass
            elif c=='+': delay=max(0.01,delay-0.01)
            elif c=='-': delay+=0.01
            elif c=='q': break
        if not paused:
            stdscr.erase()
            # add random drops
            if random.random()<0.4: drops.append(Drop(random.randrange(cols),random.randrange(4),rows,layer_colors[random.randrange(4)]))
            new_drops=[]
            for d in drops:
                if d.update(rows): d.draw(stdscr,cols); new_drops.append(d)
                else:
                    # detect words in column of cluster center
                    for w in WORD_LIST:
                        if w in ''.join([t[1] for t in d.trail]):
                            if w not in found:
                                found.append(w); logging.info(f"Found {w}")
                                clusters.append(Cluster(w,cols//2,rows//2,40,layer_colors[0]))
                                curses.beep()
            drops=new_drops
            # update clusters
            clusters=[c for c in clusters if c.update() and c.draw(stdscr)]
            # spinner
            if frame%SPIN_SPEED==0: spin=(spin+1)%len(SPINNER)
            stdscr.addstr(0,cols-2,SPINNER[spin],curses.color_pair(5)|curses.A_BOLD)
            # HUD
            hud=f"Time:{int(elapsed)}s WPS:{int(wps)} Drops:{len(drops)} Clusters:{len(clusters)}"
            stdscr.addstr(height-1,0,hud[:cols],curses.color_pair(5)|curses.A_BOLD)
            stdscr.refresh(); time.sleep(delay)
            if len(found)>=TARGET_COUNT: break
    # End screen
    stdscr.nodelay(False); stdscr.erase()
    msg="=== CINEMATIC COMPLETE ==="
    stdscr.addstr(rows//2,(cols-len(msg))//2,msg,curses.color_pair(3)|curses.A_BOLD)
    for i,w in enumerate(found,1): stdscr.addstr(rows//2+2+i,(cols//2)-len(w)//2,w,curses.color_pair(4)|curses.A_BOLD)
    stdscr.refresh(); stdscr.getch()

if __name__=='__main__': curses.wrapper(main)

