import math
from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.exceptions import HTTPException

import bcrypt
from pymongo import MongoClient
from flask_mail import Mail, Message

from datetime import timedelta
import datetime
import config
from datetime import datetime

import requests, json

app = Flask(__name__)
pais = 2  # COLOMBIA
# SETTINGS
app.secret_key = 'proyectoAhora2022COLOMBIA'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=15)
# credenciales para  email
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = 'apis2back@gmail.com'
app.config['MAIL_PASSWORD'] = 'bgjqofsrolmpjftf'

#  Conectamos a la base datos de mongo
MONGO_HOST = "200.48.235.251"   ##cambiar por localhost (127.0.0.1)
MONGO_PUERTO = "27017"  
MONGO_PWD = "ciba15153232"  ##cambiar contraseña
MONGO_USER = "estacionescolombia"  ##cambiar por root
MONGO_TIEMPO_FUERA = 10000
MONGO_BASEDATOS = "PROYECTOC" ##cambiar por nombre de la BD
MONGO_COLECCION = "users"
MONGO_URI = "mongodb://" + MONGO_USER + ":" + MONGO_PWD + \
    "@"+MONGO_HOST + ":" + MONGO_PUERTO + "/" + MONGO_BASEDATOS

client = MongoClient(MONGO_URI)
baseDatos = client[MONGO_BASEDATOS]
coleccion = baseDatos[MONGO_COLECCION]
# colección para registrar las visitas
MONGO_COLECCION_V = "VISITAS"
##
# RECAPTACHA
app.config['RECAPTCHA_ENABLED'] = False
sitekey = "6Ld3AMghAAAAAPqQ5g1Y4LqYzIknU11p2Esexhxa" #cambiar si es necesario
secret = "6Ld3AMghAAAAAEbWii0S3XUtSDGh52iApMJJMJ2p" #cambiar si es necesario


@app.route("/", methods=['post', 'get'])
def login():
    session.permanent = True
    loginForm = LoginForm()
    message = 'Please login to your account'
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        # check if email exists in database
        email_found = coleccion.find_one({"email": email})
        if email_found:
            email_val = email_found['email']
            passwordcheck = email_found['password']
            # encode the password and check if it matches
            if type(passwordcheck) == str:
                password = password.encode()
                from_node_hash = passwordcheck.encode()
                if bcrypt.hashpw(password, from_node_hash) == from_node_hash:
                    print("Ha ingresado con cuenta de móvil al aplicativo web!!!")
                    session["email"] = email_val
                    coleccion_V = baseDatos[MONGO_COLECCION_V]
                    coleccion_V.insert_one(funcionesGenerales.Visita(email))
                    return redirect(url_for('home'))
                else:
                    if "email" in session:
                        coleccion_V = baseDatos[MONGO_COLECCION_V]
                        coleccion_V.insert_one(funcionesGenerales.Visita(email))
                        return redirect(url_for("home"))
                    message = 'Error en la contraseña'
                    return render_template('accounts/login.html', message=message, form=loginForm)
            else:
                if bcrypt.checkpw(password.encode('utf-8'), passwordcheck):
                    session["email"] = email_val
                    coleccion_V = baseDatos[MONGO_COLECCION_V]
                    coleccion_V.insert_one(funcionesGenerales.Visita(email))
                    return redirect(url_for('home'))
                else:
                    if "email" in session:
                        # hay que iinsertar un JSON para contabilizar las visitas.
                        coleccion_V = baseDatos[MONGO_COLECCION_V]
                        coleccion_V.insert_one(funcionesGenerales.Visita(email))
                        return redirect(url_for("home"))
                    message = 'Error en la contraseña'
                    return render_template('accounts/login.html', message=message, form=loginForm)
        else:
            message = 'Email no encontrado'
            return render_template('accounts/login.html', message=message, form=loginForm)

    return render_template('accounts/login.html', form=loginForm)

@app.route("/register", methods=["POST", "GET"])
def register():
    form = CreateAccountForm()
    message = ''
    """ if "email" in session:
        print("en register form home")
        return redirect(url_for("home")) """
    if request.method == "POST":
        nombres = request.form.get("nombres")
        apellido_paterno = request.form.get("apellido_paterno")
        apellido_materno = request.form.get("apellido_materno")
        email = request.form.get("email")
        session["email"] = email
        fecNacimiento = request.form.get("fecNacimiento")
        ocupacion = request.form.get("ocupacion")
        asociacion = request.form.get("asociacion")
        password1 = request.form.get("password1")
        password2 = request.form.get("password2")
        captcha_response = request.form['g-recaptcha-response']
        
        if is_human(captcha_response):
            # if found in database showcase that it's found
            user_found = coleccion.find_one({"name": nombres})
            email_found = coleccion.find_one({"email": email})
            if email_found:
                #str(email_found["email"]) == email
                message = 'Este email ya existe en la base de datos'
                return render_template('accounts/register.html', message=message, form=form, sitekey=sitekey)
            
            if password1 != password2:
                message = 'Las contraseñas no coinciden!'
                return render_template('accounts/register.html', message=message, form=form, sitekey=sitekey)
            else:
                # hash the password and encode it
                hashed = bcrypt.hashpw(
                    password2.encode('utf-8'), bcrypt.gensalt())
                # assing them in a dictionary in key value pairs
                user_input = {'nombres': nombres,
                                'apellido_paterno': apellido_paterno,
                                'apellido_materno': apellido_materno,
                                'email': email,
                                'fecNacimiento': fecNacimiento,
                                'ocupacion': ocupacion,
                                'asociacion': asociacion,
                                'password': hashed}
                # insert it in the record collection
                print("insert mongo:", user_input)
                coleccion.insert_one(user_input)

                # find the new created account and its email
                user_data = coleccion.find_one({"email": email})
                new_email = user_data['email']
                # if registered redirect to logged in as the registered user
                coleccion_V = baseDatos[MONGO_COLECCION_V]
                coleccion_V.insert_one(funcionesGenerales.Visita(email))
                return render_template('home.html', email=new_email)
        else:
             # Log invalid attempts
            flash("Por favor llenar todos los campos")     
    return render_template('accounts/register.html', message=message, form=form, sitekey=sitekey)

def is_human(captcha_response):
    payload = {'response':captcha_response, 'secret':secret}
    response = requests.post("https://www.google.com/recaptcha/api/siteverify", payload)
    response_text = json.loads(response.text)
    respuesta_captacha = response_text['success']
    print("Respuesta chpcha:", respuesta_captacha)
    return response_text['success']
@app.route("/logout", methods=["POST", "GET"])
def logout():
    loginForm = LoginForm()
    if "email" in session:
        session.pop("email", None)
        return redirect(url_for('login'))
    else:
        return redirect(url_for('login'))


@app.route("/ReContraseña", methods=["POST", "GET"])
def ReContraseña():
    loginForm = LoginForm()
    if request.method == "POST":
        email = request.form.get("email")
        # actualizar contraseña
        # check if email exists in database
        email_found = coleccion.find_one({"email": email})
        if email_found:
            email_val = email_found['email']
            print("email_found:", email_found)
            print("email_val:", email_val)
            passwordcheck = email_found['password']
            print("passwordcheck:", passwordcheck)
            # actualizamos en base de datos
            password = funcionesGenerales.generate_random_string()
            # hash the password and encode it
            hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            print("Se ha actualizado")
            # enviamos el password a correo electronico del remitente
            mail = Mail(app)

            msg = Message("Cambio de contraseña -Aplicativo °AHora",
                          sender="apis2back@gmail.com", recipients=["{}".format(email)])
            msg.body = "Se ha cambiado su contraseña de manera exitosa. Por favor se recomienda cambiar a una contraseña que recuerde, ya que la contraseña que se le ha asignado es temporal, esto lo puede realizar en la opción 'Usuario' \nContraseña: {}".format(password)
            print("mensaje anexado")
            try:
                mail.send(msg)
                coleccion.update_one({"email": email}, {
                                 "$set": {"password": hashed}})
                flash("Mensaje enviado correctamente. Por favor revisar su gmail!")
                return redirect(url_for("login"))
            except:
                flash("Mensaje no enviado.")
                flash("¡Por favor intentar más tarde!")
                return redirect(url_for("login"))

        else:
            flash("email no encontrado")
    return redirect(url_for("login"))


@app.route("/ActContraseña", methods=["POST", "GET"])
def ActContraseña():
    if request.method == "POST":
        password1 = request.form.get("password1")
        password2 = request.form.get("password2")
        email = session["email"]
        if password1 != password2:
            flash('Las contraseñas no coinciden!')
            return redirect(url_for("usuario")) 
        else:
            # hash the password and encode it
            hashed = bcrypt.hashpw(
                password2.encode('utf-8'), bcrypt.gensalt())
            
            coleccion.update_one({"email": email}, {
                                 "$set": {"password": hashed}})
            flash("La contraseña fue actualizada correctamente")
        return redirect(url_for("usuario"))


@app.route('/home')
def home():
    if "email" in session:
        email = session["email"]
        return render_template('home.html', email=email)
    else:
        return redirect(url_for("login"))

@app.route('/usuario')
def usuario():
    form = LoginForm()
    email = session["email"]
    datos = coleccion.find_one({"email": email})
    nombres = datos["nombres"] + " " + \
        datos["apellido_paterno"] + " " + datos["apellido_materno"]
    ocupacion = datos["ocupacion"]
    asociacion = datos["asociacion"]
    fecNacimiento = datos["fecNacimiento"]
    if "/" in fecNacimiento:
        dl1 = fecNacimiento.split("/")
        d1 = int(dl1[0])
        m1 = int(dl1[1])
        if d1 < 10:
            day = "0" + str(d1)
        else:
            day = str(d1)
        if m1 < 10:
            month = "0" + str(m1)
        else:
            month = str(m1)
        newdate = dl1[2] + "-" + month + "-" + day
    else:
        newdate = fecNacimiento
    return render_template("usuario.html", nombres=nombres, ocupacion=ocupacion, asociacion=asociacion, email=email, fecNacimiento=newdate, form =form)

# PRIMERA FUNCIÓN
@app.route('/formNroHojas')
def formNroHojas():
    formIndicadoresCultivo = FormIndicadoresCultivo()
    return render_template('formNroHojas.html', form=formIndicadoresCultivo)


@app.route('/viewNroHojas', methods=['POST'])
def viewNroHojas():
    if request.method == 'POST':
        estacion = request.form['cmbEstacion']
        # fechaFinal=request.form['fechaFinal']
        # para colombia enviamos la fecha de hoy
        fecha_hoy = datetime.now()
        date = fecha_hoy.date()
        fechaFinal = date.strftime("%Y-%m-%d")
        ###################################
        session['estacion'] = estacion
        session['fechaFinal'] = fechaFinal
        fechaFinal = funcionesGenerales.cambiar_formato_fecha(fechaFinal)
        print("fechafinal2:", fechaFinal)
        # DICCIONARIO QUE CONTIENE LAS ESTACIONES
        dict_estaciones = {"1": "Fundación", "2": "otras"}

        estacionName = dict_estaciones[estacion]  # BUSCA LA ESTACION
        NHojas14, NHojas28, data = primeraFuncion.NumeroHojas(fechaFinal, int(estacion))
        session['estacionName'] = estacionName
        session['NHojas14'] = str(NHojas14)
        session['NHojas28'] = str(NHojas28)
        session['data'] = data

        fechas = [row[0] for row in data]
        tempPromedio = [row[1] for row in data]
        gradosDia = [row[2] for row in data]
        last_fecha = fechas[-1]
        # return render_template('viewBiomasa.html',valor1 = valor1, valor2 = valor2, valor3=valor3,  estacionName = estacionName)
        return render_template('viewNroHojas.html', NHojas14=NHojas14, NHojas28=NHojas28, data=data, fechas=fechas, last_fecha=last_fecha, tempPromedio=tempPromedio, gradosDia=gradosDia, estacionName=estacionName)


@app.route('/viewNroHojasNroSemanas', methods=['POST'])
def viewNroHojasNroSemanas():
    if request.method == 'POST':
        estacion = request.form['cmbEstacion']
        nroSemanas = request.form['nroSemanas']
        # fechaFinal=request.form['fechaFinal']
        # para colombia enviamos la fecha de hoy
        fecha_hoy = datetime.now()
        date = fecha_hoy.date()
        fechaFinal = date.strftime("%Y-%m-%d")
        ###################################
        session['fechaFinal'] = fechaFinal
        session['estacion'] = estacion
        session['nroSemanas'] = nroSemanas
        fechaFinal = funcionesGenerales.cambiar_formato_fecha(fechaFinal)
       # DICCIONARIO QUE CONTIENE LAS ESTACIONES
        dict_estaciones = {"1": "Fundación", "2": "otras"}
        estacionName = dict_estaciones[estacion]
        session['estacionName'] = estacionName
        NHojas, data = primeraFuncion.NumeroHojasSemanas(
            fechaFinal, int(estacion), int(nroSemanas))
        session['valor1'] = str(NHojas)
        session['data'] = data
        fechas = [row[0] for row in data]
        tempPromedio = [row[1] for row in data]
        gradosDia = [row[2] for row in data]
        return render_template('view14NroSemanas.html', NHojas=NHojas,  data=data, fechas=fechas, tempPromedio=tempPromedio, gradosDia=gradosDia, estacionName=estacionName, nroSemanas=nroSemanas, fechaFinal=fechaFinal)

@app.route('/formHojasHijo')
def formHojasHijo():
    formIndicadoresCultivo = FormIndicadoresHojas()
    return render_template('formHojasHijo.html', form=formIndicadoresCultivo)

@app.route('/viewHojasHijo', methods=['POST'])
def viewHojasHijo():
    if request.method == 'POST':
        fechaCosecha = request.form['fechaCosecha']
        print("cosecha:", fechaCosecha)
        estacion = request.form['cmbEstacion']
        session['estacion'] = estacion
        session['fechaCosecha'] = fechaCosecha
        fechaCosecha = funcionesGenerales.cambiar_formato_fecha(fechaCosecha)
        dict_estaciones = {"1": "Fundación", "2": "otras"}
        estacionName = dict_estaciones[estacion]
        session['estacionName'] = estacionName
        # nuevo
        valorNroHojas, dataGraficasNroHojas = segundaFuncion.EstimacionNroHojasHijo(
            fechaCosecha, int(estacion))
        session['valorNroHojas'] = str(valorNroHojas)
        session['dataGraficasNroHojas'] = dataGraficasNroHojas
        fechasNroHojas = [row[0] for row in dataGraficasNroHojas]
        tempPromedioNroHojas = [row[1] for row in dataGraficasNroHojas]
        gradosDiaNroHojas = [row[2] for row in dataGraficasNroHojas]
        # fin nuevo
        
        return render_template('viewHojasHijo.html', fechaCosecha=fechaCosecha,fechasNroHojas=fechasNroHojas, tempPromedioNroHojas=tempPromedioNroHojas, gradosDiaNroHojas=gradosDiaNroHojas, dataGraficasNroHojas=dataGraficasNroHojas, valorNroHojas=valorNroHojas, estacionName=estacionName)


# SEGUNDA FUNCIÓN

@app.route('/formIndicadoresCosecha')
def formIndicadoresCosecha():
    formIndicadoresCultivo = FormIndicadoresCultivo()
    return render_template('formIndicadoresCosecha.html', form=formIndicadoresCultivo)

@app.route('/formIndicadoresFloracion')
def formIndicadoresFloracion():
    formIndicadoresCultivo = FormIndicadoresCultivo()
    return render_template('formIndicadoresFloracion.html', form=formIndicadoresCultivo)

@app.route('/viewIndicadoresCosecha', methods=['POST'])
def viewIndicadoresCosecha():
    if request.method == 'POST':
        fechaCosecha = request.form['fechaCosecha']
        estacion = request.form['cmbEstacion']
        session['estacion'] = estacion
        session['fechaCosecha'] = fechaCosecha
        fechaCosecha = funcionesGenerales.cambiar_formato_fecha(fechaCosecha)
        dict_estaciones = {"1": "Fundación", "2": "otras"}
        estacionName = dict_estaciones[estacion]
        session['estacionName'] = estacionName
        
        # GRADOS DIA BACKWARD
        GDA, fecha_floracion, nSemanas, data = segundaFuncion.EstimacionFechaFloracion(
            fechaCosecha, int(estacion))

        session['GDA'] = str(GDA)
        session['fecha_floracion'] = str(fecha_floracion)
        session['nSemanas'] = str(nSemanas)
        session['data'] = data
        fechasBackward = [row[0] for row in data]
        tempPromedioBackward = [row[1] for row in data]
        gradosDiaBackward = [row[2] for row in data]
        return render_template('viewIndicadoresCosecha.html', fechaCosecha=fechaCosecha, GDA=GDA, fecha_floracion=fecha_floracion, nSemanas=nSemanas, fechasBackward=fechasBackward, tempPromedioBackward=tempPromedioBackward, gradosDiaBackward=gradosDiaBackward, data=data, estacionName=estacionName)

@app.route('/viewIndicadoresFloracion', methods=['POST'])
def viewIndicadoresFloracion():
    if request.method == 'POST':
        fechaFloracion = request.form['fechaFloracion']
        estacion = request.form['cmbEstacion']
        session['estacion'] = estacion
        session['fechaFloracion'] = fechaFloracion
        fechaFloracion = funcionesGenerales.cambiar_formato_fecha(
            fechaFloracion)
        dict_estaciones = {"1": "Fundación", "2": "otras"}
        estacionName = dict_estaciones[estacion]
        session['estacionName'] = estacionName
        # GRADOS DIA FORWARD
        valor1, valor2, valor3, estimacion, data, semana_total, temperatura = segundaFuncion.EstimacionFechaCosecha(
            fechaFloracion, int(estacion))
        valor1 = round(valor1)
        nroSemanas = round((int(estimacion)/7), 1)
        session['nroSemanas'] = str(nroSemanas)
        session['valor1'] = str(valor1)
        session['valor2'] = str(valor2)
        session['valor3'] = str(valor3)
        session['estimacion'] = str(estimacion)
        fechas = [row[0] for row in data]
        tempPromedio = [row[1] for row in data]
        gradosDia = [row[2] for row in data]
        Humedad = [row[3] for row in data]
        fechaFinal = data[-1][0]
        if estimacion == 0:
            file_selector = 'viewIndicadoresFloracion-1.html'

        else:
            file_selector = 'viewIndicadoresFloracion.html'

        return render_template(file_selector,  fechaFinal=fechaFinal, fechaFloracion=fechaFloracion,  valor1=valor1, valor2=valor2, valor3=valor3, fechas=fechas, tempPromedio=tempPromedio, gradosDia=gradosDia, datosCompletos=data,  estimacion=estimacion,  estacionName=estacionName, nroSemanas=nroSemanas, semana_total=semana_total, temperatura=temperatura, Humedad=Humedad)

# TERCERA FUNCION BIOMASA

@app.route('/formBiomasa')
def formBiomasa():
    formBiomasa = FormBiomasa()
    return render_template('formBiomasa.html', form=formBiomasa)

@app.route('/formBiomasaProyeccion')
def formBiomasaProyeccion():
    formBiomasa = FormBiomasa()
    return render_template('formBiomasaProyeccion.html', form=formBiomasa)

@app.route('/viewBiomasa', methods=['POST'])
def viewBiomasa():
    if request.method == 'POST':
        fechaCosecha = request.form['fechaCosecha']
        Cant_manos = request.form['Cant_manos']
        rPa = request.form['rPa']
        estacion = request.form['cmbEstacion']
        session['Cant_manos'] = Cant_manos
        session['rPa'] = rPa
        session['fechaCosecha'] = fechaCosecha
        session['estacion'] = estacion
        fechaCosecha = funcionesGenerales.cambiar_formato_fecha(fechaCosecha)
        dict_estaciones = {"1": "Fundación", "2": "otras"}
        estacionName = dict_estaciones[estacion] 
        session['estacionName'] = estacionName
        fec_string, biomasa_planta, biomasa, semanas = terceraFuncion.EstimacionRacimoCicloAnterior(
            fechaCosecha, int(estacion), int(rPa), int(Cant_manos))
        return render_template('viewBiomasa.html', fec_string=fec_string, biomasa_planta=biomasa_planta, biomasa=biomasa,  estacionName=estacionName, semanas=semanas)

@app.route('/viewBiomasaProyeccion', methods=['POST'])
def viewBiomasaProyeccion():
    if request.method == 'POST':
        fechaFloracion = request.form['fechaFloracion']
        Cant_manos = request.form['Cant_manos']
        rPa = request.form['rPa']
        estacion = request.form['cmbEstacion']
        session['Cant_manos'] = Cant_manos
        session['rPa'] = rPa
        session['fechaFloracion'] = fechaFloracion
        session['estacion'] = estacion
        fechaFloracion = funcionesGenerales.cambiar_formato_fecha(
            fechaFloracion)
        dict_estaciones = {"1": "Fundación", "2": "otras"}
        estacionName = dict_estaciones[estacion]  # BUSCA LA ESTACION
        session['estacionName'] = estacionName
        fec, fec_final, biomasa_planta, biomasa, estimacion, semanas = terceraFuncion.EstimacionRacimoProyeccion(
            fechaFloracion, int(estacion), int(rPa), int(Cant_manos))
        if estimacion == 0:
            file_selector = 'viewBiomasaProyeccion-1.html'
        else:
            file_selector = 'viewBiomasaProyeccion.html'
        return render_template(file_selector, fec=fec, fec_final=fec_final,
                               biomasa_planta=biomasa_planta, biomasa=biomasa, semanas=semanas, estimacion=estimacion,
                               estacionName=estacionName)

# CUARTA FUNCIÓN

@app.route('/formNutrientes')
def formNutrientes():
    formNutrientes = FormNutrientes()
    return render_template('formNutrientes.html', form=formNutrientes)

@app.route('/viewNutrientes', methods=['POST'])
def viewNutrientes():
    if request.method == 'POST':
        fec = request.form['fechaCosecha']
        rPa = request.form['rPa']
        intervalo = request.form['intervalo']
        estacion = request.form['cmbEstacion']
        session['rPa'] = rPa
        session['intervalo'] = intervalo
        session['estacion'] = estacion
        fechaCosecha = funcionesGenerales.cambiar_formato_fecha(fec)
        dict_estaciones = {"1": "Fundación", "2": "otras"}
        estacionName = dict_estaciones[estacion] 
        session['estacionName'] = estacionName
        fec, biomasa_planta, biomasa, tupla = cuartaFuncion.nutrientes(
            fechaCosecha, int(estacion), int(rPa), int(intervalo))
        session['fec'] = str(fec)
        session['biomasa_planta'] = str(biomasa_planta)
        session['biomasa'] = str(biomasa)
        session['tupla'] = tupla
        fechas = [row[0] for row in tupla]
        masa_kg = [row[1] for row in tupla]
        msa_ton = [row[2] for row in tupla]
        return render_template('viewNutrientes.html', fec=fec, biomasa_planta=biomasa_planta, biomasa=biomasa, tupla=tupla, intervalo=intervalo,  estacionName=estacionName)

# QUINTA FUNCIÓN

@app.route('/formHidrica')
def formHidrica():
    formRiego = FormRiego()
    return render_template('formHidrica.html', form=formRiego)

@app.route('/viewHidrica', methods=['POST'])
def viewHidricaDemanda():
    if request.method == 'POST':
        estacion = request.form['cmbEstacion']
        rPa = request.form['rPa']
        dAparente = request.form['dAparente']
        Hsuelo = request.form['Hsuelo']
        riego = request.form['cmbRiego']
        # para colombia enviamos la fecha de hoy
        fecha_hoy = datetime.now()
        date = fecha_hoy.date()
        fechaFinal = date.strftime("%Y-%m-%d")
        ###################################
        session['rPa'] = rPa
        session['dAparente'] = dAparente
        session['Hsuelo'] = Hsuelo
        session['riego'] = riego
        session['estacion'] = estacion
        session['fechaFinal'] = fechaFinal
        fechaFinal = funcionesGenerales.cambiar_formato_fecha(fechaFinal)
        dict_estaciones = {"1": "Fundación", "2": "otras"}
        estacionName = dict_estaciones[estacion]  # BUSCA LA ESTACION
        session['estacionName'] = estacionName
        Rec_LP, Rec_L_Ha, data = quintaFuncion.RecomendacionHidrica(
            fechaFinal, int(estacion), int(rPa), float(dAparente), int(Hsuelo), riego)
        session['data'] = data
        fechas = [row[0] for row in data]
        evap = [row[1] for row in data]
        rain = [row[2] for row in data]
        fechaFinal = data[-1][0]
        return render_template('viewHidrica.html', Rec_LP=Rec_LP, Rec_L_Ha=Rec_L_Ha, fechas=fechas, evap=evap, rain=rain, data=data, estacionName=estacionName, fechaFinal=fechaFinal, riego=riego)

# OTRAS FUNCIONALIDADES
@app.route('/historicos')
def historicos():
    formhistoricos = FormHistoricos()
    return render_template('formHistoricos.html', form=formhistoricos)

@app.route('/viewHistoricos', methods=['POST'])
def viewHistoricos():
    if request.method == 'POST':
        ##cosecha: 2022-09-27
        fechaInicio = request.form['fechaInicio']
        print("cosecha:", fechaInicio)
        estacion = request.form['cmbEstacion']
        session['estacion'] = estacion
        session['fechaInicio'] = fechaInicio
        fechaInicio = funcionesGenerales.cambiar_formato_fecha(fechaInicio)
        print("fecha inicio:", fechaInicio)
        dict_estaciones = {"1": "Fundación", "2": "otras"}
        estacionName = dict_estaciones[estacion]
        session['estacionName'] = estacionName
        # nuevo
        dataGraficasNroHojas = funcionesGenerales.historicos(fechaInicio, int(estacion))
        print("data:", dataGraficasNroHojas)
        session['dataGraficasNroHojas'] = dataGraficasNroHojas
        fechasNroHojas = [row[0] for row in dataGraficasNroHojas]
        temp = [row[1] for row in dataGraficasNroHojas]
        humedad = [row[2] for row in dataGraficasNroHojas]
        viento = [row[3] for row in dataGraficasNroHojas]
        radiacion = [row[4] for row in dataGraficasNroHojas]
        precipitacion = [row[5] for row in dataGraficasNroHojas]
        et = [row[6] for row in dataGraficasNroHojas]
        # fin nuevo
        
        return render_template('viewHistoricos.html', fechaInicio=fechaInicio,fechasNroHojas=fechasNroHojas, temp=temp, humedad=humedad, viento =viento,radiacion=radiacion, dataGraficasNroHojas=dataGraficasNroHojas, estacionName=estacionName)



@app.route('/EstacionesEstado')
def estaciones_estado():
    cantidad_Estaciones, Registro_Estaciones = funcionesGenerales.estado_estaciones(
        pais)
    Id_estacion = [row[0] for row in Registro_Estaciones]
    Nombre_esacion = [row[1] for row in Registro_Estaciones]
    Fecha_ultima_act = [row[2] for row in Registro_Estaciones]
    session['cantidad_Estaciones'] = cantidad_Estaciones
    session['Id_estacion'] = str(Id_estacion)
    session['Nombre_esacion'] = str(Nombre_esacion)
    session['Fecha_ultima_act'] = Fecha_ultima_act
    return render_template("estado_estaciones.html", cantidad_Estaciones=cantidad_Estaciones, Id_estacion=Id_estacion, Nombre_esacion=Nombre_esacion, Fecha_ultima_act=Fecha_ultima_act, Registro_Estaciones=Registro_Estaciones)

@app.route('/EnviarCorreo', methods=['GET', 'POST'])
def EnviarCorreo():
    # MAIL_DEFAULT_SENDER : default None
    # MAIL_MAX_EMAILS : default None
    # MAIL_SUPPRESS_SEND : default app.testing
    # MAIL_ASCII_ATTACHMENTS : default False
    mail = Mail(app)
    form = EnviarEmail()

    email = session["email"]
    datos = coleccion.find_one({"email": email})
    nombre = datos["nombres"]
    apellido_paterno = datos["apellido_paterno"]
    apellido_materno = datos["apellido_materno"]
    Dispositivo = "Laptop o Computadora"
    asociacion = datos["asociacion"]
    nombres = nombre + " " + apellido_paterno + " " + apellido_materno
    if request.method == "POST":
        mensaje = request.form.get("mensaje")
        captcha_response = request.form['g-recaptcha-response']
        if is_human(captcha_response):       
            msg = Message("Sugerencias y consultas - °AHora",
                        sender="apis2back@gmail.com", recipients=["apis2back@gmail.com"])
            msg.body = "Nombre: {} \nApellidos: {} {}\nEmail: {}\nAsociación: {}\nDispositivo remitente: {}\nMensaje:\n{}".format(
                nombre, apellido_paterno, apellido_materno, email, asociacion, Dispositivo, mensaje)
            print("mensaje anexado")
            try:
                mail.send(msg)
                print("mensaje enviado")
                return redirect(url_for("MensajeEnviado"))
            except:
                print("mensaje no enviado")
                return redirect(url_for("MensajeError"))
        else:
            flash("Por favor llenar todos los campos") 
    
    return render_template("EnviarCorreo.html", form=form,sitekey=sitekey, nombres=nombres, asociacion=asociacion, email=email)

@app.route('/MensajeEnviado', methods=['GET', 'POST'])
def MensajeEnviado():
    return render_template("MensajeEnviado.html")

@app.route('/MensajeError', methods=['GET', 'POST'])
def MensajeError():
    return render_template("MensajeError.html")

""" @app.errorhandler(Exception)
def handle_exception(e):
    # pass through HTTP errors
    if isinstance(e, HTTPException):
        return e
    # now you're handling non-HTTP exceptions only
    flash('Error: Verifique los datos ingresados')
    return render_template("formError.html", e=e), 500 

@app.before_request
def antes_de_cada_peticion():
    ruta = request.path
    print("ruta solicitada:", ruta)
    if not "email" in session  and ruta != "/login" and ruta != "/register"and ruta != "/" and ruta != "/logout"  and ruta != "/ReContraseña" and '/static/' not in ruta:
        print("ruta solicitada en if:", ruta)
        print("No se ha iniciado sesión")
        flash("Inicia sesión para continuar")
        return redirect(url_for('login'))
    else:
        print("funcionamiento correcto") """

import funcionesGenerales
import primeraFuncion
import segundaFuncion
import terceraFuncion
import cuartaFuncion
import quintaFuncion
from forms import FormIndicadoresCultivo
from forms import FormBiomasa
from forms import FormNutrientes
from forms import FormRiego
from forms import LoginForm, CreateAccountForm
from forms import EnviarEmail
from forms import FormIndicadoresHojas
from forms import FormHistoricos

if __name__ == '__main__':
    app.run(port=5000, debug=True)