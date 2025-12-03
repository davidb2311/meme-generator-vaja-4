import os
from flask import Flask, render_template, request, send_file, redirect, url_for
from PIL import Image, ImageDraw, ImageFont
import io

app = Flask(__name__)

# Configure upload and generated folders
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['GENERATED_FOLDER'] = 'generated'
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB max file size
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

# Create folders if they don't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['GENERATED_FOLDER'], exist_ok=True)

def allowed_file(filename):
    """Check if the file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def create_meme(image_path, top_text, bottom_text, output_path):
    """Create a meme by adding text to an image"""
    
    # Open the image
    img = Image.open(image_path)
    
    # Create a drawing context
    draw = ImageDraw.Draw(img)
    
    # Get image dimensions
    width, height = img.size
    
    # Load a font (using default PIL font if not available)
    try:
        # Try to load a larger font
        font_size = int(height / 10)
        font = ImageFont.truetype("arial.ttf", font_size)
    except IOError:
        # Use default font if arial is not available
        font_size = int(height / 20)
        font = ImageFont.load_default()
    
    # Function to draw outlined text (for better readability)
    def draw_outlined_text(draw_obj, position, text, font, fill_color, outline_color):
        x, y = position
        # Draw outline
        for dx in [-2, 0, 2]:
            for dy in [-2, 0, 2]:
                draw_obj.text((x+dx, y+dy), text, font=font, fill=outline_color)
        # Draw main text
        draw_obj.text(position, text, font=font, fill=fill_color)
    
    # Draw top text
    if top_text:
        # Calculate text size
        try:
            # For PIL 8.0.0+ with getbbox
            bbox = draw.textbbox((0, 0), top_text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
        except:
            # Fallback for older PIL versions
            text_width, text_height = draw.textsize(top_text, font=font)
        
        # Center the text
        x = (width - text_width) / 2
        y = 10  # Small padding from top
        
        # Draw outlined text at the top
        draw_outlined_text(draw, (x, y), top_text, font, 
                          fill_color="white", outline_color="black")
    
    # Draw bottom text
    if bottom_text:
        # Calculate text size
        try:
            # For PIL 8.0.0+ with getbbox
            bbox = draw.textbbox((0, 0), bottom_text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
        except:
            # Fallback for older PIL versions
            text_width, text_height = draw.textsize(bottom_text, font=font)
        
        # Center the text
        x = (width - text_width) / 2
        y = height - text_height - 10  # Small padding from bottom
        
        # Draw outlined text at the bottom
        draw_outlined_text(draw, (x, y), bottom_text, font, 
                          fill_color="white", outline_color="black")
    
    # Save the meme
    img.save(output_path)
    return output_path

@app.route('/', methods=['GET', 'POST'])
def index():
    """Main page with meme generator form"""
    meme_image = None
    top_text = ""
    bottom_text = ""
    
    if request.method == 'POST':
        # Check if the post request has the file part
        if 'image' not in request.files:
            return render_template('index.html', 
                                 error='No file selected',
                                 meme_image=meme_image,
                                 top_text=top_text,
                                 bottom_text=bottom_text)
        
        file = request.files['image']
        top_text = request.form.get('top_text', '')
        bottom_text = request.form.get('bottom_text', '')
        
        # If user does not select file, browser also submits an empty part
        if file.filename == '':
            return render_template('index.html', 
                                 error='No file selected',
                                 meme_image=meme_image,
                                 top_text=top_text,
                                 bottom_text=bottom_text)
        
        if file and allowed_file(file.filename):
            # Save uploaded file
            filename = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(filename)
            
            # Generate meme
            output_filename = f"meme_{os.path.basename(filename)}"
            output_path = os.path.join(app.config['GENERATED_FOLDER'], output_filename)
            
            create_meme(filename, top_text, bottom_text, output_path)
            
            # Pass the generated meme path to template
            meme_image = output_filename
            
            # Clean up uploaded file (optional)
            # os.remove(filename)
    
    return render_template('index.html', 
                         meme_image=meme_image,
                         top_text=top_text,
                         bottom_text=bottom_text)

@app.route('/download/<filename>')
def download(filename):
    """Route to download the generated meme"""
    path = os.path.join(app.config['GENERATED_FOLDER'], filename)
    return send_file(path, as_attachment=True)

@app.route('/view/<filename>')
def view_meme(filename):
    """Route to view the generated meme"""
    path = os.path.join(app.config['GENERATED_FOLDER'], filename)
    return send_file(path)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)