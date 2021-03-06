import os
import json
import urllib
import time
from random import randint
from dotenv import load_dotenv, find_dotenv
from bottle import route, view, request, response, run
from aubio import source, pitch, notes, miditofreq
from melody import Melody
from note import Note

env = os.environ.get('ENV', 'development')
if env == 'development':
    load_dotenv(find_dotenv())

@route('/', method='POST')
@view('melody')
def index():
    file = request.files.get('file')
    name, extension = os.path.splitext(file.filename)
    filename = os.path.join(os.path.dirname(__file__), 'tmp/' + time.strftime("%Y%m%d%H%M%S") + '_' + str(randint(1000000,9999999)) + '_' + name + extension)
    file.save(filename)
    downsample = int(os.environ.get('DOWNSAMPLE', 1))
    samplerate = int(os.environ.get('SAMPLERATE', 44100)) // downsample
    fft_size = int(os.environ.get('FTT_SIZE', 512)) // downsample
    hop_size = int(os.environ.get('HOP_SIZE', 256))  // downsample
    source_file = source(filename, samplerate, hop_size)
    samplerate = source_file.samplerate
    tolerance = 0.8
    pitch_o = pitch("yin", fft_size, hop_size, samplerate)
    pitch_o.set_unit("Hz")
    pitch_o.set_tolerance(tolerance)
    pitches = []
    total_frames = 0
    while True:
        samples, read = source_file()
        frequency = pitch_o(samples)[0]
        start = total_frames / float(samplerate)
        pitches += [Note(start=start, frequency=frequency)]
        total_frames += read
        if read < hop_size: break
    ending_time = total_frames / float(samplerate)
    melody = Melody(pitches=pitches, ending_time=ending_time)
    response.content_type = 'application/json'
    return dict(melody=melody)
run(host=os.environ.get('HOST', '0.0.0.0'), port=int(os.environ.get('PORT', 8080)), reloader=(os.environ.get('RELOADER', 'False') == 'True'))
