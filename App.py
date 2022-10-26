import math
from flask import Flask, jsonify, render_template, request, redirect, url_for, flash, session
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
app.config['MAIL_PASSWORD'] = 'fbjtkajygwlxnvbl'

#  Conectamos a la base datos de mongo
MONGO_HOST = "200.48.235.251"   ##cambiar por localhost (127.0.0.1)
MONGO_PUERTO = "27017"  
MONGO_PWD = "ciba15153232"  ##cambiar contraseña
MONGO_USER = "estacionescolombia"  ##cambiar por root
MONGO_TIEMPO_FUERA = 10000
MONGO_BASEDATOS = "PROYECTOC" ##cambiar por nombre de la BD
MONGO_COLECCION = "users"
MONGO_ALERT_COLECCION = "ALERTAS"
MONGO_URI = "mongodb://" + MONGO_USER + ":" + MONGO_PWD + \
    "@"+MONGO_HOST + ":" + MONGO_PUERTO + "/" + MONGO_BASEDATOS

client = MongoClient(MONGO_URI)
baseDatos = client[MONGO_BASEDATOS]
coleccion = baseDatos[MONGO_COLECCION]
alert_coleccion = baseDatos[MONGO_ALERT_COLECCION ]
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

def unix_to_string(unix_date):
    time_datetime = datetime.fromtimestamp(unix_date)
    # time_datetime = datetime.fromtimestamp(1646150400)
    fecha_date = time_datetime.date()#En formato date
    fecha_str = str(fecha_date.day)+'/'+str(fecha_date.month)+'/'+str(fecha_date.year)#Se ha convertido a formato string
    # print("Se ha impreso: ", fecha_str)

    return fecha_str

@app.route('/home')
def home():
    import time
    if "email" in session:
        email = session["email"]

        #Get the actual date in Unix (porque de esa manera las fechas de solo una unidad son 1/3/2022, lo que no se quiere es que sea 01/03/2022)
        current_unix_time = int(time.time())
        # time_datetime = datetime.fromtimestamp(current_unix_time)
        # # time_datetime = datetime.fromtimestamp(1646150400)
        # fecha_date = time_datetime.date()#En formato date
        # fecha_str = str(fecha_date.day)+'/'+str(fecha_date.month)+'/'+str(fecha_date.year)#Se ha convertido a formato string
        # print("Se ha impreso: ", fecha_str)

        fecha_str = unix_to_string(current_unix_time)

        dics = alert_coleccion.find({"fecha": fecha_str, 'intervalo': 'hora'})
        data = []
        for doc in dics:
            data.append(doc)
        print("###########DATA HOME ES: ", data)

        #Cuando se envía notificación de día, siempre es del día anterior.
        day_before = int(time.time()) - 86400
        fecha_str_before = unix_to_string(day_before)

        # dics_day = alert_coleccion.find({"fecha": "16/10/2022", 'intervalo': 'dia'})
        dics_day = alert_coleccion.find({"fecha": fecha_str_before, 'intervalo': 'dia'})
        data_day = []
        for doc in dics_day:
            data_day.append(doc)
        print("->>>>>>>>>DATA DAY ES: ", data_day)

        # Se convierten los idccionarios en tuplas:
        mensaje_hour = [tuple(d.values()) for d in data]
        mensaje_day = [tuple(d.values()) for d in data_day]

        print("MENSAJE: ", mensaje_hour)

        return render_template('home.html', email=email, mensaje_hour=mensaje_hour, mensaje_day=mensaje_day)
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
        # print("---->>> DATA GRAFICAS: ", dataGraficasNroHojas)
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
        #print("fecha inicio:", fechaInicio)
        dict_estaciones = {"1": "Fundación", "2": "otras"}
        estacionName = dict_estaciones[estacion]
        session['estacionName'] = estacionName
        # nuevo
        dataGraficasNroHojas = funcionesGenerales.historicos(fechaInicio, int(estacion))
        #print("data:", dataGraficasNroHojas)
        session['dataGraficasNroHojas'] = dataGraficasNroHojas
        fechasNroHojas = [row[0] for row in dataGraficasNroHojas]
        temp = [row[1] for row in dataGraficasNroHojas]
        humedad = [row[2] for row in dataGraficasNroHojas]
        viento = [row[3] for row in dataGraficasNroHojas]
        radiacion = [row[4] for row in dataGraficasNroHojas]
        precipitacion = [row[5] for row in dataGraficasNroHojas]
        et = [row[6] for row in dataGraficasNroHojas]
        # fin nuevo
        
        return render_template('viewHistoricos.html', fechaInicio=fechaInicio,fechasNroHojas=fechasNroHojas, temp=temp, humedad=humedad, viento =viento,radiacion=radiacion, precipitacion=precipitacion, et=et, dataGraficasNroHojas=dataGraficasNroHojas, estacionName=estacionName)



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

@app.errorhandler(Exception)
def handle_exception(e):
    # pass through HTTP errors
    if isinstance(e, HTTPException):
        return e
    # now you're handling non-HTTP exceptions only
    flash('Error: Verifique los datos ingresados')
    return render_template("formError.html", e=e), 500 

# @app.before_request
# def antes_de_cada_peticion():
#     ruta = request.path
#     print("ruta solicitada:", ruta)
#     if not "email" in session  and ruta != "/login" and ruta != "/register"and ruta != "/" and ruta != "/logout"  and ruta != "/ReContraseña" and '/static/' not in ruta:
#         print("ruta solicitada en if:", ruta)
#         print("No se ha iniciado sesión")
#         flash("Inicia sesión para continuar")
#         return redirect(url_for('login'))
#     else:
#         print("funcionamiento correcto")

@app.before_request
def antes_de_cada_peticion():
    ruta = request.path
    print("ruta solicitada:", ruta)
    if not "email" in session and ruta != "/login" and ruta != "/register"and ruta != "/" and ruta != "/logout"  and ruta != "/ReContraseña"  and ruta != "/addcontador" and ruta != "/getperfil" and ruta != "/addcomments" and ruta != "/getcomments" and ruta != "/addNroHojasHijo" and ruta != "/getNroHojasHijo" and ruta != "/addnrohojas" and ruta != "/getnrohojas" and ruta != "/getestadomet" and ruta != "/addflora" and ruta != "/getflora" and ruta != "/addcosecha" and ruta != "/getcosecha" and ruta != "/addracimo" and ruta != "/getracimo" and ruta != "/addracimoproy" and ruta != "/getracimoproy" and ruta != "/addnutrientes" and ruta != "/getnutrientes" and ruta != "/addriego" and ruta != "/getriego"and ruta != "/addMonitoreo" and ruta != "/getMonitoreo" and '/static/' not in ruta:
        print("ruta solicitada en if:", ruta)
        print("No se ha iniciado sesión")
        flash("Inicia sesión para continuar")
        return redirect(url_for('login'))
    else:
        print("funcionamiento correcto")

#####################################################################################################
############################## API PARA EL MOVIL ####################################################
#####################################################################################################

############## FUNCIÓN 1.1 - CÁLCULO DE LA CANTIDAD DEL NÚMERO DE HOJAS PLANTA HIJO ###############

@app.route('/getNroHojasHijo', methods = ['GET'])
def get_nroHojasHijo():
    import time
    from datetime import datetime
    fechas = session.get('fechas', None)
    estacion = session.get('estacion', None)
    print("La fecha elegida es: ", fechas)

    #DICCIONARIO QUE CONTIENE LAS ESTACIONES
    dict_estaciones = {"fundación": "FUNDACIÓN", "otras": "OTRAS"}
    label_estaciones = {"fundación": "1", "otras": "2"}

    punto = dict_estaciones[estacion]
    print("la estación es: ", punto)
    label_est = label_estaciones[estacion]

    #Cuando el usuario elige otras fechas.
    valorNroHojas, dataGraficasNroHojas = segundaFuncion.EstimacionNroHojasHijo(fechas, int(label_est))

    valorNroHojas = round(valorNroHojas, 1)

    fechasNroHojas = [row[0] for row in dataGraficasNroHojas]
    tempPromedioNroHojas = [row[1] for row in dataGraficasNroHojas]
    gradosDiaNroHojas = [row[2] for row in dataGraficasNroHojas]

    ##valores max y min:
    temp_max = int(max(tempPromedioNroHojas) + 2)
    temp_min = int(min(tempPromedioNroHojas) - 2)

    gdd_max = int(max(gradosDiaNroHojas) + 2)
    gdd_min = int(min(gradosDiaNroHojas) - 2)

    data_dict = []
    data_gdd = []

    for i, elem in enumerate(fechasNroHojas):
        dictionary = {}
        dict_gdd = {}
        ux = int(time.mktime(datetime.strptime(elem, "%d/%m/%Y").timetuple()))
        dictionary['x'] = ux
        dictionary['y'] = tempPromedioNroHojas[i]
        dict_gdd['x'] = ux
        dict_gdd['y'] = gradosDiaNroHojas[i]
        data_dict.append(dictionary)
        data_gdd.append(dict_gdd)
    
    if len(fechasNroHojas) == 1:
        fecha_ux = int(time.mktime(datetime.strptime(fechasNroHojas[0], "%d/%m/%Y").timetuple()))
        print("Solo hay una fecha")
    else:
        fecha_ux = ""

    # Los resultados que se van a mostrar en la segunda pantalla del aplicativo.
    result = [
                {"fechaCosecha": fechas,
                "data_dict": data_dict,
                "data_gdd": data_gdd,
                "temp_max": temp_max,
                "temp_min": temp_min,
                "gdd_max": gdd_max,
                "gdd_min": gdd_min,
                "fecha_ux": fecha_ux,
                "estacion": punto,
                "valorNroHojas": valorNroHojas,
                }
            ]

    return jsonify(result)

@app.route('/addNroHojasHijo', methods = ['POST'])
def add_nroHojasHijo():
    estacion = request.json['estacion']#La etiqueta debe llamarse igual como se ha definido los estados en el archivo .js
    fechas = request.json['fechas']
    fechas = funcionesGenerales.cambiar_formato_fecha_movil(fechas)

    session['fechas'] = fechas
    session['estacion'] = estacion

    print("Se ejecuta el POST")

    return redirect(url_for('get_nroHojasHijo'))

############## FUNCIÓN 1.2 - CÁLCULO DE LA CANTIDAD DEL NÚMERO DE HOJAS PLANTA MADRE ###############

@app.route('/getnrohojas', methods = ['GET'])
def get_nrohojas():
    import time
    estacion = session.get('estacion', None)
    days = session.get('days', None)

    #para colombia enviamos la fecha de hoy
    from datetime import datetime
    fecha_hoy = datetime.now()
    date = fecha_hoy.date()
    fechaFinal = date.strftime("%Y-%m-%d")
    #Convertimos la fecha desde yy-mm-dd a dd/mm/aa
    fechaFinal = funcionesGenerales.cambiar_formato_fecha(fechaFinal)
    print("fechafinal2:", fechaFinal)
    #Diccionario que contiene las estaciones, en otros se pueden 
    dict_estaciones = {"fundación": "FUNDACIÓN", "otras": "OTRAS"}
    label_estaciones = {"fundación": "1", "otras": "2"}

    punto = dict_estaciones[estacion]
    print("la estación es: ", punto)
    label_est = label_estaciones[estacion]
  
    if (days.endswith(".0")) or (days.endswith(".")):
        CantSemanas = int(float(days))
    else:       
        CantSemanas= int(days)

    #Cálculo de los resultados para mostrar en el aplicativo
    valor1, data = primeraFuncion.NumeroHojasSemanas(fechaFinal, int(label_est), CantSemanas)
    valor1 = round(valor1, 1)

    print("La cantidad de semanas es: ", days)

    fechas = [row[0] for row in data]
    tempPromedio = [row[1] for row in data]
    gradosDia = [row[2] for row in data]

    #valores max y min de los parámetros a mostrar en las gráficas.
    temp_max = int(max(tempPromedio) + 1)
    temp_min = int(min(tempPromedio) - 1)

    gdd_max = int(max(gradosDia) + 2)
    gdd_min = int(min(gradosDia) - 2)

    fechaActual = datetime.today()
    fechaActual = fechaActual.strftime('%d/%m/%Y')

    data_dict = []
    data_gdd = []

    for i, elem in enumerate(fechas):
        dictionary = {}
        dict_gdd = {}
        ux = int(time.mktime(datetime.strptime(elem, "%d/%m/%Y").timetuple()))
        dictionary['x'] = ux
        dictionary['y'] = tempPromedio[i]
        dict_gdd['x'] = ux
        dict_gdd['y'] = gradosDia[i]
        data_dict.append(dictionary)
        data_gdd.append(dict_gdd)   

    #Resultados para enviar a la pantalla respuesta del aplicativo.
    result = [
        {"nroHojas": valor1,
        "fechaActual": fechaActual,
        "semanas": str(days),
        "estacion": punto,
        "data_for_plot": data_dict,
        "data_gdd": data_gdd,
        "temp_max": temp_max,
        "temp_min": temp_min,
        "gdd_max": gdd_max,
        "gdd_min": gdd_min,
        }
        ]
        
    return jsonify(result)

@app.route('/addnrohojas', methods = ['POST'])
def add_nrohojas():
    days = request.json['days']
    estacion = request.json['estacion']#La etiqueta debe llamarse igual como se ha definido los estados en el archivo .js

    session['days'] = days
    session['estacion'] = estacion

    print("Se ejecuta el POST")

    return redirect(url_for('get_nrohojas'))

################ FUNCIÓN 2.1 - ESTIMACIÓN DE LA FECHA DE FLORACIÓN ########################

@app.route('/getflora', methods = ['GET'])
def get_floracion():
    import time
    from datetime import datetime
    fechaCosecha = session.get('fechas', None)
    estacion = session.get('estacion', None)
    print("La fecha elegida es: ", fechaCosecha)

    #DICCIONARIO QUE CONTIENE LAS ESTACIONES
    dict_estaciones = {"fundación": "FUNDACIÓN", "otras": "OTRAS"}
    label_estaciones = {"fundación": "1", "otras": "2"}

    punto = dict_estaciones[estacion]
    print("la estación es: ", punto)
    label_est = label_estaciones[estacion]

    # GRADOS DIA BACKWARD
    gda,fecha_floracion, nsemanas, datas = segundaFuncion.EstimacionFechaFloracion(fechaCosecha, int(label_est))

    print("El valor de GDA es: ", gda)

    fechasBackward = [row[0] for row in datas]#Lista de fechas
    tempPromedioBackward = [row[1] for row in datas]#Lista de temperatura promedio acorde a las fechas
    gradosDiaBackward = [row[2] for row in datas]#Lista de grados día acorde a las fechas

    #Valores máximos y mínimos de los parámetros:
    temp_max_back = int(max(tempPromedioBackward) + 2)
    temp_min_back = int(min(tempPromedioBackward) - 2)

    gdd_max_back = int(max(gradosDiaBackward) + 40)
    gdd_min_back = int(min(gradosDiaBackward) - 2)

    data_dict_back = []
    data_gdd_back = []

    for i, elem in enumerate(fechasBackward):
        dictionary = {}
        dict_gdd = {}
        ux = int(time.mktime(datetime.strptime(elem, "%d/%m/%Y").timetuple()))
        dictionary['x'] = ux
        dictionary['y'] = tempPromedioBackward[i]
        dict_gdd['x'] = ux
        dict_gdd['y'] = gradosDiaBackward[i]
        data_dict_back.append(dictionary)
        data_gdd_back.append(dict_gdd)
    
    result = [
                {"fechaCosecha": fechaCosecha,
                "fechaFloracion": fecha_floracion,
                "GDA": gda,
                "semanas": nsemanas,
                "estacion": punto,
                "data_dict_back": data_dict_back,
                "data_gdd_back": data_gdd_back,
                "temp_max_back": temp_max_back,
                "temp_min_back": temp_min_back,
                "gdd_max_back": gdd_max_back,
                "gdd_min_back": gdd_min_back,
                }
            ]

    return jsonify(result)

@app.route('/addflora', methods = ['POST'])
def add_floracion():
    estacion = request.json['estacion']#La etiqueta debe llamarse igual como se ha definido los estados en el archivo .js
    fechas = request.json['fechas']

    fechas = funcionesGenerales.cambiar_formato_fecha_movil(fechas)

    session['fechas'] = fechas
    session['estacion'] = estacion

    print("Se ejecuta el POST")

    return redirect(url_for('get_floracion'))

################ FUNCIÓN 2.2 - ESTIMACIÓN DE LA FECHA DE COSECHA ########################

@app.route('/getcosecha', methods = ['GET'])
def get_cosecha():
    import time
    from datetime import datetime
    fechaFloracion = session.get('fechas', None)
    estacion = session.get('estacion', None)

    #DICCIONARIO QUE CONTIENE LAS ESTACIONES
    dict_estaciones = {"fundación": "FUNDACIÓN", "otras": "OTRAS"}
    label_estaciones = {"fundación": "1", "otras": "2"}

    punto = dict_estaciones[estacion]
    # print("la estación es: ", punto)
    label_est = label_estaciones[estacion]
    
    # GRADOS DIA FORWARD
    gda,fecha_floracion, fecha_cosecha, estimacion, datas, semana_total, temperatura = segundaFuncion.EstimacionFechaCosecha(fechaFloracion, int(label_est))
    gda = round(gda)
    nroSemanas = round((int(estimacion)/7),1)
    # print("El valor de GDD es: ", valor1)


    fechasForward = [row[0] for row in datas]#lista de fechas obtenidas del cálculo
    tempPromedioForward = [row[1] for row in datas]#Lista de tempertaura promedio
    gradosDiaForward = [row[2] for row in datas]#Lista de grados día
    humedadForward = [row[3] for row in datas]#Lista de humedad

    # sizeFechas = len(fechasForward)
    # print("La lista de fechas es: ",fechasForward)
    # print("La cantidad de fechas es: ", str(sizeFechas))

    #Valores máximos y mínimos de los parámetros:
    temp_max_for = int(max(tempPromedioForward) + 2)
    temp_min_for = int(min(tempPromedioForward) - 2)

    gdd_max_for = int(max(gradosDiaForward) + 30)
    gdd_min_for = int(min(gradosDiaForward) - 2)

    hum_max_for = int(max(humedadForward) + 2)
    hum_min_for = int(min(humedadForward) - 2)

    ## Diccionario para los parámetros:
    data_dict_for = []
    data_gdd_for = []
    data_hum_for = []

    for i, elem in enumerate(fechasForward):
        dictionary = {}
        dict_gdd = {}
        dict_hum = {}
        ux = int(time.mktime(datetime.strptime(elem, "%d/%m/%Y").timetuple()))
        dictionary['x'] = ux
        dictionary['y'] = tempPromedioForward[i]
        dict_gdd['x'] = ux
        dict_gdd['y'] = gradosDiaForward[i]
        dict_hum['x'] = ux
        dict_hum['y'] = humedadForward[i]
        data_dict_for.append(dictionary)
        data_gdd_for.append(dict_gdd)
        data_hum_for.append(dict_hum)

    if len(fechasForward) == 1:
        fecha_ux = int(time.mktime(datetime.strptime(fechasForward[0], "%d/%m/%Y").timetuple()))
        print("Solo hay una fecha")
    else:
        fecha_ux = ""


    result = [
                {"fechaFloracion": fecha_floracion,
                "fechaCosecha": fecha_cosecha,
                "GDA": gda,
                "diasEstimados": estimacion,
                "semanas": nroSemanas,
                "estacion": punto,
                "data_dict_for": data_dict_for,
                "data_gdd_for": data_gdd_for,
                "data_hum_for": data_hum_for,
                "temp_max_for": temp_max_for,
                "temp_min_for": temp_min_for,
                "gdd_max_for": gdd_max_for,
                "gdd_min_for": gdd_min_for,
                "hum_max_for": hum_max_for,
                "hum_min_for": hum_min_for,
                "fecha_ux": fecha_ux,
                }
            ]

    return jsonify(result)

@app.route('/addcosecha', methods = ['POST'])
def add_cosecha():
    estacion = request.json['estacion']#La etiqueta debe llamarse igual como se ha definido los estados en el archivo .js
    fechas = request.json['fechas']
    fechas = funcionesGenerales.cambiar_formato_fecha_movil(fechas)

    session['fechas'] = fechas
    session['estacion'] = estacion
    print("Se ejecuta el POST")

    return redirect(url_for('get_cosecha'))


############## FUNCIÓN 3.1 - PESO DE RACIMO PASADO EN CICLOS ANTERIORES ####################

@app.route('/getracimo', methods = ['GET'])
def get_racimo():
    import time
    from datetime import datetime
    fechaCosecha = session.get('fechas', None)
    nroManos = session.get('manos', None)
    denPlantas = session.get('denPlant', None)
    estacion = session.get('estacion', None)
    print("La fecha elegida es: ", fechaCosecha)

    #DICCIONARIO QUE CONTIENE LAS ESTACIONES
    dict_estaciones = {"fundación": "FUNDACIÓN", "otras": "OTRAS"}
    label_estaciones = {"fundación": "1", "otras": "2"}

    punto = dict_estaciones[estacion]
    print("la estación es: ", punto)
    label_est = label_estaciones[estacion]

        # Cálculo de respuestas para peso de racimo de ciclos anteriores
    fec_cosecha, biomasa_planta, biomasa, semanas = terceraFuncion.EstimacionRacimoCicloAnterior(fechaCosecha, int(label_est), int(denPlantas), int(nroManos))
    biomasa_planta = round(biomasa_planta,2)

    # print("tipo de valor 4 es: ", type(valor2))
    
    result = [
                {
                "fechaCosecha": fec_cosecha,
                "kgPlanta": biomasa_planta,
                "valor3": biomasa,
                "estacion": punto,
                }
            ]

    return jsonify(result)

@app.route('/addracimo', methods = ['POST'])
def add_racimo():
    estacion = request.json['estacion']#La etiqueta debe llamarse igual como se ha definido los estados en el archivo .js
    fechas = request.json['fechas']
    manos = request.json['manos']
    denPlant = request.json['matas']
    fechas = funcionesGenerales.cambiar_formato_fecha_movil(fechas)

    session['fechas'] = fechas
    session['denPlant'] = denPlant
    session['estacion'] = estacion
    session['manos'] = manos
    print("Se ejecuta el POST")

    return redirect(url_for('get_racimo'))

######################### FUNCIÓN 3.2  - PROYECCIÓN PESO DE RACIMO #########################

@app.route('/getracimoproy', methods = ['GET'])
def get_racimoproy():
    fechaFloracion = session.get('fechas', None)
    nroManos = session.get('manos', None)
    denPlantas = session.get('denPlant', None)
    estacion = session.get('estacion', None)
    # print("La fecha elegida es: ", fechas)

    #DICCIONARIO QUE CONTIENE LAS ESTACIONES
    dict_estaciones = {"fundación": "FUNDACIÓN", "otras": "OTRAS"}
    label_estaciones = {"fundación": "1", "otras": "2"}

    punto = dict_estaciones[estacion]
    print("la estación es: ", punto)
    label_est = label_estaciones[estacion]

    # Obtención de valores para responder, frente al cálculo de proyección de peso de racimo
    fec, fec_final,biomasa_planta, biomasa, estimacion, semanas = terceraFuncion.EstimacionRacimoProyeccion(fechaFloracion, int(label_est), int(denPlantas), int(nroManos))
    
    result = [
                {
                "fechaFloracion": fec,
                "biomasaPlanta": biomasa_planta,
                "biomasa": biomasa,
                "estacion": punto,
                "fec_final": fec_final,
                "estimacion": estimacion,
                "semanas": semanas,
                }
            ]

    return jsonify(result)

@app.route('/addracimoproy', methods = ['POST'])
def add_racimoproy():
    estacion = request.json['estacion']#La etiqueta debe llamarse igual como se ha definido los estados en el archivo .js
    fechas = request.json['fechas']
    manos = request.json['manos']
    denPlant = request.json['matas']
    fechas = funcionesGenerales.cambiar_formato_fecha_movil(fechas)

    session['fechas'] = fechas
    session['denPlant'] = denPlant
    session['estacion'] = estacion
    session['manos'] = manos
    print("Se ejecuta el POST")
    print("variable denplant: ", denPlant)

    return redirect(url_for('get_racimoproy'))

############## FUNCIÓN 4 - CANTIDAD DE NUTRIENTES A REPONER ####################

@app.route('/getnutrientes', methods = ['GET'])
def get_nutrientes():
    fechaCosecha = session.get('fechas', None)
    denPlantas = session.get('denPlant', None)
    semanasRacimo = session.get('semanasRacimo', None)
    estacion = session.get('estacion', None)
    print("La fecha elegida es: ", fechaCosecha)
    
    if (semanasRacimo.endswith(".0")) or (semanasRacimo.endswith(".")):
        CantSemanRacimo = int(float(semanasRacimo))
    else:       
        CantSemanRacimo = int(semanasRacimo)

    #DICCIONARIO QUE CONTIENE LAS ESTACIONES
    dict_estaciones = {"fundación": "FUNDACIÓN", "otras": "OTRAS"}
    label_estaciones = {"fundación": "1", "otras": "2"}

    punto = dict_estaciones[estacion]
    print("la estación es: ", punto)
    label_est = label_estaciones[estacion]

    # Obtención de una tupla que contiene las cantidades de cada nutriente a reponer
    _, _, _, tupla = cuartaFuncion.nutrientes(fechaCosecha, int(label_est), int(denPlantas), CantSemanRacimo)

    #Se convierte la tupla a lista
    nutrientesList = [list(row) for row in tupla]

    print("la lista de datos es", nutrientesList)
    
    result = [
                {
                "nutrientes": nutrientesList,
                "estacion": punto,
                }
            ]

    return jsonify(result)

@app.route('/addnutrientes', methods = ['POST'])
def add_nutrientes():
    estacion = request.json['estacion']#La etiqueta debe llamarse igual como se ha definido los estados en el archivo .js
    fechas = request.json['fechas']
    denPlant = request.json['matas']
    semanasRacimo = request.json['semanaRacimo']
    fechas = funcionesGenerales.cambiar_formato_fecha_movil(fechas)

    session['fechas'] = fechas
    session['denPlant'] = denPlant
    session['semanasRacimo'] = semanasRacimo
    session['estacion'] = estacion
    print("Se ejecuta el POST")

    return redirect(url_for('get_nutrientes'))


########################## FUNCIÓN 5 - DEMANDA DE RIEGO #########################

@app.route('/getriego', methods = ['GET'])
def get_riego():
    import time
    from datetime import datetime
    denPlantas = "2000"
    sisriego = session.get('sisriego', None)
    densidad = session.get('densidad', None)
    estacion = session.get('estacion', None)
    humedad = session.get('humedad', None)
    #######################################################para colombia enviamos la fecha de hoy
    fecha_hoy = datetime.now()
    date = fecha_hoy.date()
    fechaFinal = date.strftime("%Y-%m-%d")
    ###################################
    fechaFinal = funcionesGenerales.cambiar_formato_fecha(fechaFinal)

    #DICCIONARIO QUE CONTIENE LAS ESTACIONES
    dict_estaciones = {"fundación": "FUNDACIÓN", "otras": "OTRAS"}
    label_estaciones = {"fundación": "1", "otras": "2"}

    punto = dict_estaciones[estacion]
    print("la estación es: ", punto)
    label_est = label_estaciones[estacion]

    # Obtención de respuestas para el cálculo de la demanda de agua
    Rec_LP, Rec_L_Ha, datas = quintaFuncion.RecomendacionHidrica(fechaFinal, int(label_est), int(denPlantas), float(densidad), int(humedad), sisriego)

    # Listas de los parámetros que se usarán para graficar
    fechasRiego = [row[0] for row in datas]
    evap = [row[1] for row in datas]
    rain = [row[2] for row in datas]
    fechaFinal=datas[-1][0]

    #Valores máximos y mínimos de los parámetros
    evap_max = int(max(evap) + 2)
    evap_min = int(min(evap) - 1)

    rain_max = int(max(rain) + 5)
    rain_min = int(min(rain) - 1)

    ## Diccionario para almacenar los parámetros a graficar
    data_dict = []
    data_rain = []

    for i, elem in enumerate(fechasRiego):
        dictionary = {}
        dict_rain = {}
        ux = int(time.mktime(datetime.strptime(elem, "%d/%m/%Y").timetuple()))
        dictionary['x'] = ux
        dictionary['y'] = evap[i]
        dict_rain['x'] = ux
        dict_rain['y'] = rain[i]
        data_dict.append(dictionary)
        data_rain.append(dict_rain)

    # Data a enviar a la pantalla de respuesta
    result = [
                {
                "valor1": Rec_LP,
                "valor2": Rec_L_Ha,
                "estacion": punto,
                "riego": sisriego,
                "data_dict": data_dict,
                "data_rain": data_rain,
                "evap_max": evap_max,
                "evap_min": evap_min,
                "rain_max": rain_max,
                "rain_min": rain_min,
                }
            ]

    return jsonify(result)

@app.route('/addriego', methods = ['POST'])
def add_riego():
    estacion = request.json['estacion']#La etiqueta debe llamarse igual como se ha definido los estados en el archivo .js
    # denPlant = request.json['matas']
    sisriego = request.json['sisriego']
    humedad = request.json['humedad']
    densidad = request.json['densidad']

    # session['denPlant'] = denPlant
    session['sisriego'] = sisriego
    session['humedad'] = humedad
    session['densidad'] = densidad
    session['estacion'] = estacion
    print("Se ejecuta el POST")

    return redirect(url_for('get_riego'))

##################   VER DATOS HISTÓRICOS: MONITOREO DE VARIABLES CLIMÁTICAS #########################

@app.route('/getMonitoreo', methods = ['GET'])
def get_MonitoreoClima():
    import time
    from datetime import datetime
    fechas = session.get('fechas', None)
    estacion = session.get('estacion', None)
    print("La fecha elegida es: ", fechas)

    #DICCIONARIO QUE CONTIENE LAS ESTACIONES
    dict_estaciones = {"fundación": "FUNDACIÓN", "otras": "OTRAS"}
    label_estaciones = {"fundación": "1", "otras": "2"}

    punto = dict_estaciones[estacion]
    print("la estación es: ", punto)
    label_est = label_estaciones[estacion]

    #SE EXTRAEN LOS DATOS DE TODAS LAS VARIABLES CLIMÁTICAS
    dataGraficasNroHojas = funcionesGenerales.historicos(fechas, int(label_est))
    fechasNroHojas = [row[0] for row in dataGraficasNroHojas]
    temp = [row[1] for row in dataGraficasNroHojas]
    humedad = [row[2] for row in dataGraficasNroHojas]
    viento = [row[3] for row in dataGraficasNroHojas]
    radiacion = [row[4] for row in dataGraficasNroHojas]
    precipitacion = [row[5] for row in dataGraficasNroHojas]
    et = [row[6] for row in dataGraficasNroHojas]


    ##valores max y min:
    temp_max = int(max(temp) + 2)
    temp_min = int(min(temp) - 2)

    hum_max = int(max(humedad) + 2)
    hum_min = int(min(humedad) - 2)

    velViento_max = int(max(viento) + 2)
    velViento_min = int(min(viento) - 2)

    rad_max = int(max(radiacion) + 100)
    rad_min = int(min(radiacion) - 2)

    rain_max = int(max(precipitacion) + 5)
    rain_min = int(min(precipitacion) - 2)

    evt_max = int(max(et) + 2)
    evt_min = int(min(et) - 2)

    #Diccionarios vacíos
    data_temp = []
    data_hum = []
    data_velViento = []
    data_rad = []
    data_rain = []
    data_evt = []

    for i, elem in enumerate(fechasNroHojas):
        dict_temp = {}
        dict_hum = {}
        dict_velViento = {}
        dict_rad = {}
        dict_rain = {}
        dict_evt = {}

        ux = int(time.mktime(datetime.strptime(elem, "%d/%m/%Y").timetuple()))

        dict_temp['x'] = ux
        dict_temp['y'] = temp[i]
        dict_hum['x'] = ux
        dict_hum['y'] = humedad[i]
        dict_velViento['x'] = ux
        dict_velViento['y'] = viento[i]
        dict_rad['x'] = ux
        dict_rad['y'] = radiacion[i]
        dict_rain['x'] = ux
        dict_rain['y'] = precipitacion[i]
        dict_evt['x'] = ux
        dict_evt['y'] = et[i]

        data_temp.append(dict_temp)
        data_hum.append(dict_hum)
        data_velViento.append(dict_velViento)
        data_rad.append(dict_rad)
        data_rain.append(dict_rain)
        data_evt.append(dict_evt)
    
    if len(fechasNroHojas) == 1:
        fecha_ux = int(time.mktime(datetime.strptime(fechasNroHojas[0], "%d/%m/%Y").timetuple()))
        print("Solo hay una fecha")
    else:
        fecha_ux = ""

    # Los resultados que se van a mostrar en la segunda pantalla del aplicativo.
    result = [
                {
                "data_temp": data_temp,
                "data_hum": data_hum,
                "data_velViento": data_velViento,
                "data_rad": data_rad,
                "data_rain": data_rain,
                "data_evt": data_evt,
                "temp_max": temp_max,
                "temp_min": temp_min,
                "hum_max": hum_max,
                "hum_min": hum_min,
                "velViento_max": velViento_max,
                "velViento_min": velViento_min,
                "rad_max": rad_max,
                "rad_min": rad_min,
                "rain_max": rain_max,
                "rain_min": rain_min,
                "evt_max": evt_max,
                "evt_min": evt_min,
                "fecha_ux": fecha_ux,
                "estacion": punto,
                }
            ]

    return jsonify(result)

@app.route('/addMonitoreo', methods = ['POST'])
def add_MonitoreoClima():
    estacion = request.json['estacion']#La etiqueta debe llamarse igual como se ha definido los estados en el archivo .js
    fechas = request.json['fechas']
    fechas = funcionesGenerales.cambiar_formato_fecha_movil(fechas)

    session['fechas'] = fechas
    session['estacion'] = estacion

    print("Se ejecuta el POST")

    return redirect(url_for('get_MonitoreoClima'))

######################################################
######################################################


############## COMENTARIOS Y SUGERENCIAS DE USUARIOS #######################


# # correo_send = 'labsac2022@gmail.com'
# # correo_send = 'userahoracolombia@labsac.com'
correo_sender = 'apis2back@gmail.com'#Este correo debe ser de el administrador principal del aplicativo, para recibir los mensajes que los usuarios envién por medio del aplicativo.

@app.route('/addcomments', methods = ['POST'])
def add_comments():
    mail = Mail(app)
    correo_send  = correo_sender
    usuario = request.json['usuario']#La etiqueta debe llamarse igual como se ha definido los estados en el archivo .js
    correo = request.json['mail']
    grupo = request.json['grupo']
    comentario = request.json['descripcion']

    #  Cuerpo del mensaje
    mensaje = 'Usuario: ' + usuario + '\n' + 'Email: ' + correo + '\n' + 'Asociación: ' + grupo + '\n' + 'Dispositivo: Móvil' + '\n' +  'Mensaje: ' + comentario

    print(mensaje)
    ## ENVIAR Email
    msg = Message("Sugerencias y consultas - °AHora", sender=correo_send, recipients=[correo_send])
    msg.body = mensaje
    mail.send(msg)

    print("Mensaje enviado")
    # session['fechas'] = fechas
    session['usuario'] = usuario
    session['correo'] = correo
    session['grupo'] = grupo
    session['comentario'] = comentario
    print("Se ejecuta el POST")

    return redirect(url_for('get_comments'))

#La ruta get para comments no devuelve ningún valor, pero se coloca para que la ruta post funcione correctamente.
@app.route('/getcomments', methods = ['GET'])
def get_comments():
    import time
    from datetime import datetime
    # fechas = session.get('fechas', None)
    usuario = session.get('usuario', None)
    correo = session.get('correo', None)
    grupo = session.get('grupo', None)
    comentario = session.get('comentario', None)

    result = [
                {
                }
            ]

    return jsonify(result)

######################################################
###########    CONTADOR VISITAS  #####################
######################################################

@app.route('/addcontador', methods = ['POST'])
def add_contador():
    from datetime import timezone
    nombre_usuario = request.json['nombres']
    mail_usuario = request.json['email']
    primer_apellido = request.json['apellido_paterno']
    segundo_apellido = request.json['apellido_materno']
    ocupacion = request.json['ocupacion']
    asociacion = request.json['asociacion']
    fecNacimiento = request.json['fecNacimiento']

    # utc_fecha = str(fecha_visita_utc)

    session['nombre_usuario'] = nombre_usuario
    session['mail_usuario'] = mail_usuario
    session['primer_apellido'] = primer_apellido
    session['segundo_apellido'] = segundo_apellido
    session['ocupacion'] = ocupacion
    session['asociacion'] = asociacion
    session['fecNacimiento_usuario'] = fecNacimiento


    fecha_utc = datetime.now(timezone.utc)

    dispositivo = 'Móvil'

    print(str(nombre_usuario) + " ha visitado el aplicativo, el día " + str(fecha_utc) + " mediante su " + str(dispositivo))

    coleccion_V = baseDatos[MONGO_COLECCION_V]

    coleccion_V.insert_one(funcionesGenerales.Visita_movil(mail_usuario))

    print("Su correo es: ", mail_usuario)
    print("Fecha utc: ", fecha_utc)
    print("NAME USUARIO: ", nombre_usuario)
    print("Fecha de nacimiento es: ", fecNacimiento)

    return redirect(url_for('get_perfil'))


@app.route('/getperfil', methods = ['GET'])
def get_perfil():
    import time
    from datetime import datetime
    #Se obtienen datos de la pantalla Home
    nombre_usuario = session.get('nombre_usuario', None)
    mail_usuario = session.get('mail_usuario', None)
    primer_apellido = session.get('primer_apellido', None)
    segundo_apellido = session.get('segundo_apellido', None)
    ocupacion = session.get('ocupacion', None)
    asociacion = session.get('asociacion', None)
    fecNacimiento = session.get('fecNacimiento_usuario', None)

    print("NAME USUARIO: ", nombre_usuario)
    print("fecha de naciemiento es: ", fecNacimiento)

    apellidos = str(primer_apellido) + " " + str(segundo_apellido)

    if " " in nombre_usuario:
        string_list = nombre_usuario.split()
        name = string_list[0]
    else:
        name = nombre_usuario

    texto_de_avatar = str(name) + " " + str(primer_apellido)

    #Función para ordenar las fechas de dd-mm-aaaa a dd/mm/aaaa o viceversa
    if "-" in fecNacimiento:
        dl1 = fecNacimiento.split("-")
        dateOfBirth = dl1[2] + "/" + dl1[1] + "/" + dl1[0]
    else:
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

        dateOfBirth = day + "/" + month + "/" + dl1[2]

    print("Fecha de nacimiento en PERFIL ES: ", dateOfBirth)
    
    result = [
                {
                "texto_de_avatar": texto_de_avatar,
                "nombre_usuario": nombre_usuario,
                "apellidos": apellidos,
                "mail_usuario": mail_usuario,
                "ocupacion": ocupacion,
                "asociacion": asociacion,
                "dateOfBirth": dateOfBirth,
                }
            ]

    return jsonify(result)

######################################################################

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

# if __name__ == '__main__':
#     app.run(host="172.20.31.172", port=5000, debug=True)

# if __name__ == '__main__':
#     app.run(host="172.20.10.4", port=5000, debug=True)