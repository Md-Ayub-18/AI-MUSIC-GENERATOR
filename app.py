"""
Ultra-Simple Music Generator - Only Flask & midiutil
FIXED VERSION - Proper HTML linking
"""
import os
import random
import math
from datetime import datetime
from flask import Flask, render_template, request, send_file, jsonify, send_from_directory
from midiutil import MIDIFile

app = Flask(__name__)
app.config['SECRET_KEY'] = 'music-generator-secret'

# Create necessary directories
os.makedirs('static', exist_ok=True)
os.makedirs('static/output', exist_ok=True)
os.makedirs('templates', exist_ok=True)

# Music configuration
MOOD_SCALES = {
    'happy': [60, 62, 64, 65, 67, 69, 71],  # C Major
    'sad': [60, 62, 63, 65, 67, 68, 70],    # C Minor
    'calm': [60, 62, 64, 66, 67, 69, 71],   # C Lydian
    'energetic': [60, 62, 64, 65, 67, 69, 71, 72],  # C Major + octave
}

GENRE_INSTRUMENTS = {
    'pop': 0,      # Piano
    'rock': 30,    # Distortion Guitar
    'jazz': 1,     # Bright Piano
    'electronic': 81,  # Square Lead
}

def generate_melody(mood, style):
    """Generate simple melody without numpy"""
    scale = MOOD_SCALES.get(mood, MOOD_SCALES['happy'])
    melody = []
    current_note = random.choice(scale)
    
    for _ in range(16):  # 16 notes
        melody.append(current_note)
        
        # Simple random walk
        if random.random() < 0.7:
            # Move within scale
            if current_note in scale:
                idx = scale.index(current_note)
                if random.random() < 0.5 and idx > 0:
                    current_note = scale[idx - 1]
                elif idx < len(scale) - 1:
                    current_note = scale[idx + 1]
        else:
            current_note = random.choice(scale)
    
    # Add variation for complex style
    if style == 'complex':
        new_melody = []
        for note in melody:
            if random.random() < 0.3:
                new_melody.append(note + 12)  # Octave up
            else:
                new_melody.append(note)
        melody = new_melody
    
    return melody

def create_midi_file(melody, tempo, instrument, filename):
    """Create MIDI file - this always works!"""
    midi = MIDIFile(1)
    track = 0
    time = 0
    
    midi.addTrackName(track, time, "AI Generated Music")
    midi.addTempo(track, time, tempo)
    midi.addProgramChange(track, 0, 0, instrument)
    
    # Add melody notes
    for note in melody:
        duration = 1 if random.random() < 0.7 else 0.5
        velocity = random.randint(80, 110)
        midi.addNote(track, 0, note, time, duration, velocity)
        time += duration
    
    # Add some bass notes (simplified)
    time = 0
    for i in range(0, len(melody), 2):
        bass_note = melody[i] - 12  # One octave lower
        if bass_note > 0:
            midi.addNote(track, 0, bass_note, time, 2, 90)
        time += 2
    
    # Save file
    filepath = f'static/output/{filename}'
    with open(filepath, 'wb') as f:
        midi.writeFile(f)
    
    return filepath

def create_simple_wav_file(melody, tempo, filename):
    """
    Create a VERY simple WAV file without numpy/scipy
    Using basic Python to create raw audio data
    """
    filepath = f'static/output/{filename}'
    
    try:
        sample_rate = 44100
        duration_per_note = 60 / tempo
        
        # We'll create a dummy WAV file that can be played
        # This is a simplified version that creates a basic tone
        
        with open(filepath, 'wb') as f:
            # Calculate total duration
            total_duration = len(melody) * duration_per_note
            
            # Create minimal WAV header (44 bytes)
            # This creates a silent WAV file that browsers can play
            num_samples = int(sample_rate * total_duration)
            
            # RIFF header
            f.write(b'RIFF')
            f.write((36 + num_samples * 2).to_bytes(4, 'little'))  # File size
            f.write(b'WAVE')
            
            # fmt chunk
            f.write(b'fmt ')
            f.write((16).to_bytes(4, 'little'))  # Chunk size
            f.write((1).to_bytes(2, 'little'))   # Audio format (PCM)
            f.write((1).to_bytes(2, 'little'))   # Mono
            f.write(sample_rate.to_bytes(4, 'little'))  # Sample rate
            f.write((sample_rate * 2).to_bytes(4, 'little'))  # Byte rate
            f.write((2).to_bytes(2, 'little'))   # Block align
            f.write((16).to_bytes(2, 'little'))  # Bits per sample
            
            # data chunk
            f.write(b'data')
            f.write((num_samples * 2).to_bytes(4, 'little'))  # Data size
            
            # Generate simple sine wave data
            for i in range(num_samples):
                t = i / sample_rate
                # Create a simple tone based on the melody
                note_index = int(t / duration_per_note) % len(melody)
                note = melody[note_index] if note_index < len(melody) else melody[0]
                frequency = 440.0 * (2 ** ((note - 69) / 12.0))
                
                # Simple sine wave
                value = int(32767 * 0.3 * math.sin(2 * math.pi * frequency * t))
                
                # Write 16-bit sample (little endian)
                f.write(value.to_bytes(2, 'little', signed=True))
        
        return filepath
    except Exception as e:
        print(f"WAV creation error (using fallback): {e}")
        # If WAV fails, just return the MIDI file path
        return None

@app.route('/')
def index():
    """Homepage"""
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    """Generate music"""
    try:
        # Get form data
        mood = request.form.get('mood', 'happy')
        genre = request.form.get('genre', 'pop')
        tempo = int(request.form.get('tempo', 120))
        style = request.form.get('style', 'simple')
        
        # Validate
        if tempo < 60 or tempo > 200:
            tempo = 120
        
        # Generate melody
        melody = generate_melody(mood, style)
        instrument = GENRE_INSTRUMENTS.get(genre, 0)
        
        # Create timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create files
        midi_filename = f"music_{timestamp}.mid"
        wav_filename = f"music_{timestamp}.wav"
        
        # Create MIDI file (always works)
        midi_path = create_midi_file(melody, tempo, instrument, midi_filename)
        midi_url = f'/static/output/{midi_filename}'
        
        # Try to create WAV file
        wav_path = create_simple_wav_file(melody, tempo, wav_filename)
        wav_url = f'/static/output/{wav_filename}' if wav_path else None
        
        # If WAV failed, use MIDI as fallback for audio player
        audio_url = wav_url if wav_url else midi_url
        
        # Prepare context for template
        context = {
            'mood': mood,
            'genre': genre,
            'tempo': tempo,
            'style': style,
            'audio_file': audio_url,
            'midi_file': midi_url,
            'wav_available': wav_url is not None,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        return render_template('result.html', **context)
    
    except Exception as e:
        return f"Error: {str(e)}", 500

@app.route('/download/<filename>')
def download(filename):
    """Download generated file"""
    return send_from_directory('static/output', filename, as_attachment=True)

@app.route('/health')
def health():
    """Health check"""
    return jsonify({
        'status': 'healthy',
        'service': 'Simple Music Generator',
        'libraries': ['Flask', 'midiutil']
    })

if __name__ == '__main__':
    print("=" * 50)
    print("Simple Music Generator")
    print("Server starting on http://127.0.0.1:5000")
    print("=" * 50)
    app.run(debug=True, port=5000)