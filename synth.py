import pygame
import numpy as np
import sys
import sounddevice as sd
from tkinter.filedialog import askopenfilename
import scipy
import tkinter.filedialog as tf
import time
import matplotlib.pyplot as plt
import math

# Initialize Pygame for easy display & user input
pygame.init()

# Set up the window
width, height = 800, 600
window = pygame.display.set_mode((width, height), pygame.RESIZABLE)
pygame.display.set_caption("synth")

# Generate data points for the starter sine wave
num_points = 44100
def generateSin(samples, freq, duration):
    x = np.linspace(0, duration, samples*duration)
    y = np.sin(2 * np.pi * freq * x)
    return y

sample_rate = 44100
starting_freq = 200
duration = 3
y_values = (generateSin(sample_rate, starting_freq, duration) + generateSin(sample_rate, 3/2*starting_freq, duration) + generateSin(sample_rate, 81/64*starting_freq, duration))/3
print('starting frequencies: ', str(starting_freq), str(81/64*starting_freq), str(3/2*starting_freq))

#text variables
font = pygame.font.SysFont('arial', 20)

# Dragging variables
dragging = False
initial_drag = True
drag_rect = pygame.Rect(0,0,0,0)
right_dragging = False

# Set up colors
black = (0, 0, 0)
white = (255, 255, 255, 150)
green = (0, 255, 0)
transparent = (0,0,0,0)
blue = (0,0,255)

#viewing window
scale = 1
start_sample = 0
toggle_follow = False
freq_domain = False

#scan line
is_playing = False
start_time = 0
total_duration = 1

#history -- for reverting back changes
history = []
history_index = 0

sorted_fft_freq = 0

# Main game loop
running = True
while running:
    #handle button inputs
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            print(event.key)
            if event.key == pygame.K_ESCAPE:    #'esc' button pressed -- exit
                running = False
            elif event.key == 107:    #'k' button pressed -- draw a plot
                print('k pressed')
                vals = np.linspace(1,100,200)
                plt.plot(range(len(vals)), vals)
                plt.show()
            elif event.key == 103:    #'g' button pressed -- add a sine wave at 40
                print('adding sine wave')
                selected_region = y_values[drag_rect.left*scale+start_sample:drag_rect.right*scale+1+start_sample]
                print(len(selected_region))
            elif event.key == 114:    #'r' button pressed -- return to sample 0
                start_sample = 0
            elif event.key == 112:    #'p' button pressed -- play the sound
                if is_playing:
                    sd.stop()
                    is_playing = False
                else:
                    sd.play(y_values, sample_rate)
                    start_time = time.time()
                    is_playing = True
            elif event.key == 102:    #'f' button pressed -- compute fft of selected region
                selected_region = y_values[drag_rect.left*scale+start_sample:drag_rect.right*scale+1+start_sample]    #compute selected region
                fft_result = np.fft.fft(selected_region)    #fft of region
                fft_freq = np.fft.fftfreq(len(selected_region), 1/sample_rate)  #calculate corresponding frequencies
                sorted_indices = np.argsort(fft_freq)   #sort the frequencies and corresponding fft
                sorted_fft_freq = fft_freq[sorted_indices]
                sorted_fft_result = fft_result[sorted_indices]
                mask = sorted_fft_freq >= 0     #select only positive frequencies
                reduced_freq = sorted_fft_freq[mask]
                sorted_fft_result = sorted_fft_result[mask]
                print(sorted_fft_freq)
                y_values = -np.abs(sorted_fft_result)/np.max(sorted_fft_result)

                inverse = np.fft.ifft(sorted_fft_result)
                #plt.plot(range(len(inverse)), -inverse)
                #plt.show()
                freq_domain = True
                start_sample = 0
            elif event.key == 122:    #'z' button pressed -- set the selected range to 0
                history.append(y_values)
                y_values[drag_rect.left*scale+start_sample:drag_rect.right*scale+1+start_sample] = 0
            elif event.key == 108:    #'l' button pressed -- load a wav file
                filename = askopenfilename()
                if filename:
                    try:
                        data = scipy.io.wavfile.read(filename)
                    except:
                        print('improperly formatted data file')
                        break
                    sample_rate = data[0]
                    if data[1].ndim != 1:
                        print('more dims')
                        y_values = data[1][:,0]
                    else:
                        print('one dim')
                        y_values = data[1]
                    y_values = y_values/np.max(y_values)    #normalize the amplitude to 1
                    y_values = y_values - np.mean(y_values)    #center on mean
            elif event.key == 101:    #'e' button pressed -- export to wave
                print('exporting')
                file_path = tf.asksaveasfilename(defaultextension=".wav", filetypes=[("Wav files", "*.wav")])
                print(file_path)
                if file_path:
                    scipy.io.wavfile.write(file_path, sample_rate, y_values)
            elif event.key == 122 and pygame.key.get_mods() & pygame.KMOD_CTRL:     #'ctrl z' -- undo
                print('undo')
            elif event.key == 114 and pygame.key.get_mods() & pygame.KMOD_CTRL:     #'ctrl r' -- redo
                print('redo')
            elif event.key == 109:      #'m' -- toggle follow
                toggle_follow = not toggle_follow
        elif event.type == pygame.MOUSEBUTTONDOWN:
            #print(event.button)
            if event.button == 4:  # Scroll up
                scale += 1
            elif event.button == 5:  # Scroll down
                scale -= 1
                if scale <= 0:
                    scale = 1
            elif event.button == 1:  # Left mouse button for dragging
                dragging = True
                start_drag_y = event.pos[1]
                start_drag_y_value = y_values.copy()
            elif event.button == 3:  # Right mouse button for dragging
                right_dragging = True
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:  # Left mouse button released
                dragging = False
            elif event.button == 3:
                right_dragging = False

    #handle dragging
    mouse = pygame.mouse.get_pos()
    if dragging:
        if initial_drag == True:    #on the first drag
            drag_rect.update(mouse[0], mouse[1], 10, 10)    #set the top left corner
            initial_drag = False
        else:    #on the other drag frames...
            drag_rect.update(drag_rect.left, drag_rect.top, mouse[0] - drag_rect.left, mouse[1] - drag_rect.top)
    else:
        initial_drag = True

    if right_dragging:
        difference = mouse[0] - prev_mouse[0]
        start_sample = np.max([1, start_sample - difference*scale])
    prev_mouse = mouse

    #wipe screen
    window.fill(black)

    #render mouse text
    if freq_domain:
        if mouse[0]*scale+start_sample < len(reduced_freq):
            text = font.render('frequency num: ' + str(reduced_freq[mouse[0]*scale+start_sample]), True, white, transparent)
    else:
        text = font.render('sample num: ' + str(mouse[0]*scale+start_sample), True, white, transparent)
    textRect = text.get_rect()
    textRect.center = (window.get_width()-100, window.get_height()-20)
    window.blit(text, textRect)

    #render scale text
    text = font.render('scale: ' + str(scale), True, white, transparent)
    textRect = text.get_rect()
    textRect.center = (window.get_width()-400, window.get_height()-20)
    window.blit(text, textRect)

    #render drag box text
    text = font.render('selected range: ' + str(drag_rect.left*scale+start_sample) + "-" + str(drag_rect.right*scale+start_sample), True, white, transparent)
    textRect = text.get_rect()
    textRect.center = (window.get_width()-600, window.get_height()-20)
    window.blit(text, textRect)

    #calculate viewing window
    y_viewing = y_values[start_sample::scale]*window.get_height()/5 + window.get_height()/2 #downsample, scale up,offset to middle of screen
    max_points = np.min([len(y_viewing), window.get_width()])
    y_viewing = y_viewing[:max_points]
    x = range(len(y_viewing))
    #print(x)
    #plotting the sound samples
    for i in range(len(y_viewing)-1):
        #print((x[i], y_viewing[i]))
        pygame.draw.line(window, (255, 255, 255), (x[i], y_viewing[i]), (x[i + 1], y_viewing[i + 1]))

    #draw scan line
    if is_playing:
        current_time = time.time() - start_time
        location = sample_rate/scale*current_time - start_sample/scale
        #print(location)
        if location > 1:
            pygame.draw.line(window, blue, (location,window.get_height()/5), (location, 4*window.get_height()/5))
        if current_time > len(y_values)/sample_rate:
            is_playing = False
        #move screen if following
        if toggle_follow:
            current_sample = current_time*sample_rate
            if current_sample > window.get_width()*scale/2:
                start_sample = math.floor(current_sample - window.get_width()*scale/2)

    pygame.draw.rect(window, green, drag_rect, width=1) #dragging window
    pygame.display.update()

# Quit Pygame
pygame.quit()
sys.exit()
