from flask import Flask, flash, render_template, request, redirect, send_from_directory, session, url_for
import os
import hashlib
import database as db
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB


template_dir = os.path.dirname(os.path.abspath(os.path.dirname(__file__)))
template_dir = os.path.join(template_dir, 'src', 'templates')
IMG_FOLDER = os.path.join('static', 'IMG')

app = Flask(__name__, template_folder = template_dir)
app.secret_key = 'clave_de_sesion'

# Cargar el conjunto de datos etiquetados de noticias reales y falsas
df = pd.read_csv('datos_noticias.csv')

# Dividir los datos en entrenamiento y prueba
X_train, X_test, y_train, y_test = train_test_split(df['texto'], df['etiqueta'], test_size=0.2, random_state=42)

# Crear un objeto CountVectorizer para convertir los textos en vectores numéricos
vectorizer = CountVectorizer(stop_words='english')
X_train_vectorized = vectorizer.fit_transform(X_train)

# Entrenar el clasificador Naive Bayes
classifier = MultinomialNB()
classifier.fit(X_train_vectorized, y_train)

# Función para clasificar una noticia dada
def clasificar_noticia(texto):
    texto_vectorizado = vectorizer.transform([texto])
    resultado = classifier.predict(texto_vectorizado)[0]
    if resultado == 0:
        return 'Noticia verdadera'
    else:
         return 'Noticia falsa'

#rutas de la aplicacion
@app.route('/')
def home():
    session.pop('username', None)
    return render_template('index.html')

#noticias
@app.route('/noticia')
def noticia():

    return render_template('new.html')


#renderizar imagenes
@app.route('/IMG/<nombre_imagen>')
def renderizar_imagen(nombre_imagen):
    ruta_imagen = f'IMG/{nombre_imagen}'
    return send_from_directory('static', ruta_imagen)

#registro de usuarios
@app.route('/registro')
def registro():
    return render_template('registro.html')

#Registro de usuarios a la plataforma con metodos has de seguridad para las contrasenas
@app.route('/registro', methods=["POST"])
def agregar():
    nombre = request.form['nombre']
    correo = request.form['email']
    contrasena = request.form['contrasena']
    contrasenav = request.form['contrasena2']
    hcontrasena = hashlib.md5(contrasena.encode()) #hash de las contrasenas
    hcontrasenav = hashlib.md5(contrasenav.encode())#hash de las contrasenas

    if correo and nombre and contrasena and contrasenav:
        cursor = db.database.cursor()
        sql = "INSERT INTO usuario (nombre, correo, contrasena, contrasenaV) VALUES (%s, %s, %s, %s)"
        data = (nombre, correo, hcontrasena.hexdigest(), hcontrasenav.hexdigest())
        cursor.execute(sql, data)
        db.database.commit()

    return redirect(url_for('home'))

#login a la aplicacion
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['email']
        password = request.form['contrasena']
        hpassword = hashlib.md5(password.encode())

        # Verificar las credenciales en la base de datos
        cursor = db.database.cursor()
        cursor.execute('SELECT * FROM fakenews.usuario WHERE correo=%s AND contrasena=%s', (username, hpassword.hexdigest()))
        user = cursor.fetchone()

        if user:
            session['username'] = user[1]
            return redirect(url_for('noticia'))
        else:
                flash('Contraseña incorrecta o usario no existe.', 'error')
                return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('home'))

#analisis de datos

@app.route('/new', methods=['GET', 'POST'])
def new():
    if request.method == 'POST':
        noticia = request.form['noticia']
        fuente  = request.form['fuente']
        fecha = request.form['fecha']

        # Ejemplo de clasificación de una noticia
        texto_noticia = noticia
        resultado = clasificar_noticia(texto_noticia)
        print(resultado)
        if resultado == 'Noticia verdadera':
            mensaje = 'verdadera'
        else:
            mensaje = 'falsa'
        # Guardar noticia
        cursor = db.database.cursor()
        sql = "INSERT INTO noticia (contenido, resultado, fuente, fecha) VALUES (%s, %s, %s, %s)"
        data = (noticia, resultado, fuente, fecha)
        cursor.execute(sql, data)
        db.database.commit()

    return render_template('new.html', mensaje=mensaje)


if __name__ == '__main__':
    app.run(debug=True, port=4000)
