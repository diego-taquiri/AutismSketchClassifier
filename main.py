import tempfile
import os
from flask import Flask, request, redirect, send_file, session
from skimage import io
import base64
import glob
import numpy as np

app = Flask(__name__)
app.secret_key = 'supersecretkey'

# Lista de categorías de dibujo y enlaces de imágenes
categories = [
    "Con ojos negros",
    "Con una sonrisa exageradamente grande",
    "Sin presencia de cejas",
    "Con ojos exageradamente distanciados",
    "Dibujos Presquemáticos (dibujar solo con círculos)",
    "Añadir un cuello a la cara",
    "Dibujar con Shaky lines exagerados"
]

image_links = [
    "https://i.postimg.cc/0yn902wd/Ojos-negros.png",
    "https://i.postimg.cc/T3mX1LnM/Sonrisa-exageradamente-grande.png",
    "https://i.postimg.cc/L8kzmDCc/Sin-cejas.png",
    "https://i.postimg.cc/wBPQ7MzJ/Ojos-separados.png",
    "https://i.postimg.cc/XJF8y5nF/Preesquematico.png",
    "https://i.postimg.cc/7Y134DLH/Con-cuello.png",
    "https://i.postimg.cc/JhZ6jjhm/Shaky-lines.png"
]

main_html = """
<html>
<head></head>
<script>
  var mousePressed = false;
  var lastX, lastY;
  var ctx;

  function InitThis() {
      ctx = document.getElementById('myCanvas').getContext("2d");
      document.getElementById('mensaje').innerHTML = 'Dibuja únicamente la cara de esta persona: ' + document.getElementById('category').value;

      $('#myCanvas').mousedown(function (e) {
          mousePressed = true;
          Draw(e.pageX - $(this).offset().left, e.pageY - $(this).offset().top, false);
      });

      $('#myCanvas').mousemove(function (e) {
          if (mousePressed) {
              Draw(e.pageX - $(this).offset().left, e.pageY - $(this).offset().top, true);
          }
      });

      $('#myCanvas').mouseup(function (e) {
          mousePressed = false;
      });
      $('#myCanvas').mouseleave(function (e) {
          mousePressed = false;
      });
  }

  function Draw(x, y, isDown) {
      if (isDown) {
          ctx.beginPath();
          ctx.strokeStyle = 'black';
          ctx.lineWidth = 6;
          ctx.lineJoin = "round";
          ctx.moveTo(lastX, lastY);
          ctx.lineTo(x, y);
          ctx.closePath();
          ctx.stroke();
      }
      lastX = x; lastY = y;
  }

  function clearArea() {
      ctx.setTransform(1, 0, 0, 1, 0, 0);
      ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height);
  }

  function prepareImg() {
     var canvas = document.getElementById('myCanvas');
     document.getElementById('myImage').value = canvas.toDataURL();
     downloadImage(canvas.toDataURL(), 'dibujo.png');
  }

  function downloadImage(data, filename = 'untitled.png') {
      var a = document.createElement('a');
      a.href = data;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
  }
</script>
<body onload="InitThis();">
    <script src="https://ajax.googleapis.com/ajax/libs/jquery/1.7.1/jquery.min.js" type="text/javascript"></script>
    <div align="center">
        <h1 id="mensaje">Dibujando...</h1>
        <img src="{{ image_url }}" alt="Imagen de una cara" width="200"/>
        <canvas id="myCanvas" width="200" height="200" style="border:2px solid black"></canvas>
        <br/>
        <br/>
        <button onclick="javascript:clearArea();return false;">Borrar</button>
    </div>
    <div align="center">
      <form method="post" action="upload" onsubmit="javascript:prepareImg();" enctype="multipart/form-data">
      <input id="category" name="category" type="hidden" value="{{ category }}">
      <input id="myImage" name="myImage" type="hidden" value="">
      <input id="bt_upload" type="submit" value="Enviar">
      </form>
    </div>
</body>
</html>
"""

@app.route("/")
def main():
    if 'category_index' not in session:
        session['category_index'] = 0
    category_index = session['category_index']
    category = categories[category_index]
    image_url = image_links[category_index]
    return main_html.replace('{{ category }}', category).replace('{{ image_url }}', image_url)

@app.route('/upload', methods=['POST'])
def upload():
    try:
        img_data = request.form.get('myImage').replace("data:image/png;base64,", "")
        category = request.form.get('category')
        if not os.path.exists(category):
            os.mkdir(category)
        with tempfile.NamedTemporaryFile(delete=False, mode="w+b", suffix='.png', dir=category) as fh:
            fh.write(base64.b64decode(img_data))
        print("Image uploaded")
    except Exception as err:
        print("Error occurred")
        print(err)

    # Increment category index after successful upload
    session['category_index'] = (session.get('category_index', 0) + 1) % len(categories)
    return redirect("/", code=302)

@app.route('/prepare', methods=['GET'])
def prepare_dataset():
    images = []
    digits = []
    for category in categories:
        filelist = glob.glob('{}/*.png'.format(category))
        images_read = io.concatenate_images(io.imread_collection(filelist))
        images_read = images_read[:, :, :, 3]  # Assuming PNG with alpha channel
        digits_read = np.array([category] * images_read.shape[0])
        images.append(images_read)
        digits.append(digits_read)
    images = np.vstack(images)
    digits = np.concatenate(digits)
    np.save('X.npy', images)
    np.save('y.npy', digits)
    return "OK!"

@app.route('/X.npy', methods=['GET'])
def download_X():
    return send_file('./X.npy')

@app.route('/y.npy', methods=['GET'])
def download_y():
    return send_file('./y.npy')

if __name__ == "__main__":
    for category in categories:
        if not os.path.exists(category):
            os.mkdir(category)
    app.run()



