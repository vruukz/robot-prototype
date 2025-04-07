import speech_recognition as sr
import openai
import pygame
import webrtcvad
import wave
import pyaudio
import os
import time
from gtts import gTTS
from langdetect import detect
from pytube import YouTube
import RPi.GPIO as GPIO

# Initialize the recognizer
recognizer = sr.Recognizer()

# OpenAI API key
openai.api_key = 'your_api_key'

# Initialize pygame mixer for playing audio
pygame.mixer.init()

# Initialize WebRTC VAD
vad = webrtcvad.Vad()
vad.set_mode(1)

# Define GPIO to LCD mapping
LCD_RS = 5
LCD_E = 6
LCD_D4 = 13
LCD_D5 = 19
LCD_D6 = 26
LCD_D7 = 21

# Define some device constants
LCD_WIDTH = 16     # Maximum characters per line
LCD_CHR = True     # Mode - Sending data
LCD_CMD = False    # Mode - Sending command

# Timing constants
E_PULSE = 0.0005
E_DELAY = 0.0005

def lcd_init():
    # Initialise display
    lcd_byte(0x33, LCD_CMD)  # 110011 Initialise
    lcd_byte(0x32, LCD_CMD)  # 110010 Initialise
    lcd_byte(0x06, LCD_CMD)  # 000110 Cursor move direction
    lcd_byte(0x0C, LCD_CMD)  # 001100 Display On, Cursor Off, Blink Off
    lcd_byte(0x28, LCD_CMD)  # 101000 Data length, number of lines, font size
    lcd_byte(0x01, LCD_CMD)  # 000001 Clear display
    time.sleep(E_DELAY)

def lcd_byte(bits, mode):
    # Send byte to data pins
    # bits = data
    # mode = True  for character
    #        False for command

    GPIO.output(LCD_RS, mode)  # RS

    # High bits
    GPIO.output(LCD_D4, False)
    GPIO.output(LCD_D5, False)
    GPIO.output(LCD_D6, False)
    GPIO.output(LCD_D7, False)
    if bits & 0x10 == 0x10:
        GPIO.output(LCD_D4, True)
    if bits & 0x20 == 0x20:
        GPIO.output(LCD_D5, True)
    if bits & 0x40 == 0x40:
        GPIO.output(LCD_D6, True)
    if bits & 0x80 == 0x80:
        GPIO.output(LCD_D7, True)

    # Toggle 'Enable' pin
    lcd_toggle_enable()

    # Low bits
    GPIO.output(LCD_D4, False)
    GPIO.output(LCD_D5, False)
    GPIO.output(LCD_D6, False)
    GPIO.output(LCD_D7, False)
    if bits & 0x01 == 0x01:
        GPIO.output(LCD_D4, True)
    if bits & 0x02 == 0x02:
        GPIO.output(LCD_D5, True)
    if bits & 0x04 == 0x04:
        GPIO.output(LCD_D6, True)
    if bits & 0x08 == 0x08:
        GPIO.output(LCD_D7, True)

    # Toggle 'Enable' pin
    lcd_toggle_enable()

def lcd_toggle_enable():
    # Toggle enable
    time.sleep(E_DELAY)
    GPIO.output(LCD_E, True)
    time.sleep(E_PULSE)
    GPIO.output(LCD_E, False)
    time.sleep(E_DELAY)

def lcd_string(message, line):
    # Send string to display
    if line == 1:
        lcd_byte(0x80, LCD_CMD)
    if line == 2:
        lcd_byte(0xC0, LCD_CMD)

    for i in range(LCD_WIDTH):
        if i < len(message):
            lcd_byte(ord(message[i]), LCD_CHR)
        else:
            lcd_byte(ord(' '), LCD_CHR)

# Function to play audio
def play_audio(file_path):
    pygame.mixer.music.load(file_path)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)

# Function for text-to-speech using gTTS with language detection
def speak(text):
    lang = detect(text)
    tts = gTTS(text=text, lang=lang)
    tts.save('response.mp3')
    play_audio('response.mp3')
    os.remove('response.mp3')

# Function to recognize speech using OpenAI Whisper model
def recognize_speech(audio_data):
    try:
        audio_file_path = "audio.wav"
        with open(audio_file_path, "wb") as f:
            f.write(audio_data.get_wav_data())
        
        response = openai.Audio.transcribe("whisper-1", file=open(audio_file_path, "rb"))
        return response['text']
    except Exception as e:
        print("Error recognizing speech:", str(e))
        return None
    finally:
        if os.path.exists(audio_file_path):
            os.remove(audio_file_path)

# Function to listen for the wake word and then process speech
def listen_for_wake_word():
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(LCD_E, GPIO.OUT)
    GPIO.setup(LCD_RS, GPIO.OUT)
    GPIO.setup(LCD_D4, GPIO.OUT)
    GPIO.setup(LCD_D5, GPIO.OUT)
    GPIO.setup(LCD_D6, GPIO.OUT)
    GPIO.setup(LCD_D7, GPIO.OUT)
    lcd_init()

    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source)
        print("Listening for wake word...")
        while True:
            try:
                lcd_string("     0    0     ", 1)
                lcd_string("        V       ", 2)
                audio = recognizer.listen(source)
                wake_word = recognizer.recognize_google(audio).lower()
                if "hello" in wake_word:
                    print("Wake word detected. Listening...")
                    play_audio('wake_sound.mp3')  # Play a short sound for wake-up call
                    lcd_string("     o    o     ", 1)
                    lcd_string("        o       ", 2)
                    speak("Yes?")
                    time.sleep(3)  # Display wake-up face for 3 seconds
                    process_speech()
                    lcd_string("     0    0     ", 1)
                    lcd_string("        V       ", 2)
            except sr.UnknownValueError:
                continue

# Function to process speech
def process_speech():
    with sr.Microphone() as source:
        print("Listening for command...")
        audio_data = recognizer.listen(source)
        text = recognize_speech(audio_data)
        if text:
            print("You said:", text)
            if "play music from youtube" in text.lower():
                # Extract the YouTube URL from the command
                url = text.lower().split("play music from youtube ")[-1].strip()
                play_youtube_audio(url)
            else:
                response = get_response(text)
                if response:
                    speak(response)

# Function to get response from OpenAI GPT
def get_response(prompt):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message['content'].strip()
    except Exception as e:
        print("Error getting response:", str(e))
        return None

# Function to download and play YouTube audio
def play_youtube_audio(url):
    yt = YouTube(url)
    stream = yt.streams.filter(only_audio=True).first()
    output_file = stream.download(output_path=".")
    base, ext = os.path.splitext(output_file)
    new_file = base + '.mp3'
    os.rename(output_file, new_file)
    play_audio(new_file)
    os.remove(new_file)

if __name__ == "__main__":
    # Ensure there's a wake sound available
    if not os.path.exists('wake_sound.mp3'):
        tts = gTTS(text="Yes?", lang='en')
        tts.save('wake_sound.mp3')
    
    try:
        listen_for_wake_word()
    except KeyboardInterrupt:
        print("Program terminated by user")
    finally:
        pygame.quit()
