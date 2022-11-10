#bibliotecas API v2
import collections
import hashlib
import hmac
import time
import numpy as np
from numpy.core.defchararray import array
#bibliotecas de rquests API
import requests
import json
# import mysql.connector
# from mysql.connector import Error
import datetime
import numpy as np
#bibliotecas delta

from datetime import timedelta
#import datetime

import sys
import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

#biblioteca Mongo
import pymongo
from pymongo import MongoClient
from bson.json_util import dumps, loads 

#Enviar correo a usuarios notificando una alerta
#Dar formato a la etiqueta de estación
dict_estaciones = {"1": "FUNDACION", "2": "OTRAS"}
ALERT_COLECCION = "ALERTAS"
#Crendenciales GMAIL
# from_address = "apis2back@gmail.com"
# password = "fbjtkajygwlxnvbl"
from_address = "servicioaplicativo22@gmail.com"
password = "gibwktbvjyxrahug"

# MONGO_HOST = "200.48.235.251"
MONGO_HOST = "192.168.34.10"
# MONGO_HOST = "127.0.0.1"
MONGO_PUERTO ="27017"
MONGO_PWD = "ciba15153232"
MONGO_USER = "root"
MONGO_TIEMPO_FUERA =1000
MONGO_URI = "mongodb://"+ MONGO_USER +":"+ MONGO_PWD + "@"+MONGO_HOST +":" + MONGO_PUERTO + "/"
print("Mongo_uri:", MONGO_URI, type(MONGO_URI))

MONGO_BASEDATOS = "PROYECTOC"
MONGO_COLECCION = "ESTACIONES"

def Mensaje_Json(temp_actual,x,y):
    try:
        unix1=x
        unix2=y
        fecha1=print("fecha Inicio:",datetime.datetime.fromtimestamp(unix1)," :",x)
        fecha2=print("fecha Final:",datetime.datetime.fromtimestamp(unix2), " :",y)
        #fecha3=print("Hora actual", datetime.datetime.fromtimestamp(t1), " :",t1)
        parameters = {
            "station-id": "17053", 
            "api-key": "xfcmxbygmi25nixeutcubwk0fcteh7vn",
            "t": temp_actual,
            "start-timestamp": x,
            "end-timestamp": y,
            "api-secret": "upqnnlalw6bst8hgszrmvkhd0tniwcmq"
        }
        parameters = collections.OrderedDict(sorted(parameters.items()))
        apiSecret = parameters["api-secret"]
        parameters.pop("api-secret", None)
        data = ""
        ####
        for key in parameters:
            #print("data:",data)
            data = data + key + str(parameters[key])
            apiSignature = hmac.new( apiSecret.encode('utf-8'), data.encode('utf-8'),hashlib.sha256).hexdigest()
            #print("key:",key)
            #print("parametros:",str(parameters[key]))
            #print("apiSignature:",apiSignature)
            url = 'https://api.weatherlink.com/v2/historic/{}?api-key={}&t={}&start-timestamp={}&end-timestamp={}&api-signature={}'.format(parameters["station-id"], parameters["api-key"], parameters["t"],parameters["start-timestamp"],parameters["end-timestamp"], apiSignature) 
            #print(url)
            response = requests.get(url, params=None) #accedes a la pagina web y al API
            
            if response.status_code == 200:
                data_banano = json.loads(response.content)
                #print("data banano_1:",data_banano)
                return(data_banano)
    except:
        print("Error Funcion Mensaje Json")
def test(data_banano):
    ##testeamos si existen datos
    try:
        indice = data_banano['sensors']
        sensor1 =indice[0]
        datoss = sensor1['data']
        if datoss == []:
            ##print("No hay datos nuevos")
            return("Nothing")
            #time.sleep(120)
        elif datoss != []:#lectura e insercion de datos
            ##print("hay datos que inscribir")
            return("Data")
    except:
        print("error en la obtencion del json") 

def fechas_Inicio_fin():
    temp_actual=int(time.time())
    ##rango de tiempo a solicitar
    x=  int(temp_actual-59*60) #tiempo 1 para encontrar el ultimo dato
    y=  int(temp_actual + 0) #fin  12:00 am 6/6/2020
    return temp_actual,x,y
def ultimo_registro(data_banano):
    ##extraemos el tiempo del JSOn
    indice = data_banano['sensors']
    #print("indice json", indice, type(indice), np.shape(indice))
    sensor1 =indice[0]
    #print("sensor1:", sensor1)
    unix_dato=int(sensor1['data'][0]['ts'])
    print("Unix de api:", unix_dato)
    ##extraemos el tiempo del ultimo registro insertado
    try:
        cliente = MongoClient(MONGO_URI, serverSelectionTimeoutMS=MONGO_TIEMPO_FUERA)
        #cliente = MongoClient(MONGO_HOST, MONGO_PUERTO)
        baseDatos = cliente[MONGO_BASEDATOS]
        coleccion=baseDatos[MONGO_COLECCION]
        cursor_UR = coleccion.find().limit(1).sort([("$natural", -1)])
        #consulta_UR = coleccion.find({"sensors.data.ts":{"$gt":1}}).limit(1).sort([("$natural", -1)])
        #consulta_UR = coleccion.find().sort({"_id":-1})
        json_cursor_UR = list(cursor_UR)[0]
        print("ultimo de BD_:", json_cursor_UR)
        unix_registro = int(json_cursor_UR["time"])
        if unix_dato != unix_registro:
            if (unix_dato - unix_registro)==3600:
                return("New date", unix_dato, unix_registro)
            else:
                return("New dateR", unix_dato, unix_registro)

        else:
            return("Date exist", 0, 0)

    except pymongo.errors.ServerSelectionTimeoutError as errorTiempo:
        return("Teimpo exedido"+ errorTiempo)
    except pymongo.errors.ConnectionFailure as errorConnexion:
        return("Fallo al conectarse a mongodb" + errorConnexion) 
def datos_a_recuperar(unix_dato, unix_registro):
    nroDatos=int((unix_dato-unix_registro)/(60*60))
    return nroDatos
def analisis_recuperacion(Datos_perdidos):
    if Datos_perdidos > 24:
        dias = Datos_perdidos//24
        restante = int(Datos_perdidos-dias*24)
        return dias, restante
    else:
        return int(0), Datos_perdidos

def Para_datos_nulos(Id,time):
    sensores=[
    ##ISS(sensor 2), nodo1 (sensor3), nodo2 (sensor13 NODO2)
    {'pais':2, 'estacion': 1,'lsid': 57386, 'time': time, 'datos': [{'wind_speed_avg': None, 'wind_speed_hi': None, 'wind_chill': None, 'solar_rad_hi': None, 'deg_days_heat': None, 'bar': None, 'hum_out': None, 'temp_out': None, 'temp_out_lo': None, 'wet_bulb': None, 'temp_out_hi': None, 'solar_rad_avg': None, 'wind_run': None, 'solar_energy': None, 'dew_point_out': None, 'heat_index_out': None, 'thsw_index': None, 'rainfall_mm': None, 'deg_days_cool': None, 'rain_rate_hi_mm': None, 'et': None}]}
    ]
        #Para la verificación 
        #[s1:31, s2:38, s3:16, s4:3, s5: 4, s6:30, s7: 30, s8:30, s9:4, s10: 4, s11: 4, s12: 4,s13: 16, s14:30, s15:4 ]
    #print("sensores:", type(sensores), len(sensores))
    contador=0
    for h in sensores:
        contador=contador+1
        #print("h:",h, type(h))
        #print("________")
        #entramos a data
        id_sensor = h["lsid"]
        #print("ID SENSOR:",id_sensor, type(id_sensor))
        if id_sensor == Id:
            return(contador,h)

def RellenarConDatosBlanco(Id,time):
    sensores=[
        {'pais':2, 'estacion': 1,"lsid":57386, "data": [{'iss_reception': None, 'wind_speed_avg': None, 'wind_speed_hi': None, 'wind_dir_of_hi': None, 'wind_chill': None, 'solar_rad_hi': None, 'deg_days_heat': None, 'thw_index': None, 'bar': None, 'hum_out': None, 'temp_out': None, 'temp_out_lo': None, 'wet_bulb': None, 'temp_out_hi': None, 'solar_rad_avg': None, 'bar_alt': None, 'arch_int': None, 'wind_run': None, 'solar_energy': None, 'dew_point_out': None, 'rain_rate_hi_clicks': None, 'wind_dir_of_prevail': None, 'et': None, 'air_density': None, 'rainfall_in': None, 'heat_index_out': None, 'thsw_index': None, 'rainfall_mm': None, 'night_cloud_cover': None, 'deg_days_cool': None, 'rain_rate_hi_in': None, 'wind_num_samples': None, 'emc': None, 'rain_rate_hi_mm':None , 'rev_type': None, 'rainfall_clicks': None, 'ts': time, 'abs_press':None}]},
        ]

        #Para la verificación 
        #[s1:31, s2:38, s3:16, s4:3, s5: 4, s6:30, s7: 30, s8:30, s9:4, s10: 4, s11: 4, s12: 4,s13: 16, s14:30, s15:4 ]
    #print("sensores:", type(sensores), len(sensores))
    contador=0
    for h in sensores:
        contador=contador+1
        #print("h:",h, type(h))
        #print("________")
        #entramos a data
        id_sensor = h["lsid"]
        #print("ID SENSOR:",id_sensor, type(id_sensor))
        if id_sensor == Id:
            dat=h["data"]
            #print("______")
            #print("Dat", dat[0], type(dat[0]))
            #print("_____")
            return(contador,dat[0])
def extra_registros(k, lsid):
###retorna la cantidad de registros
    if lsid==57386: #sensor 2
        #print("--> registro ({}):".format(count_Re), k)
        lista=["bar","temp_out","temp_out_hi","temp_out_lo", "hum_out", #se han separado de 5
                "dew_point_out","wet_bulb", "wind_run","wind_speed_avg","wind_speed_hi",
                "wind_chill","heat_index_out","rainfall_mm","rain_rate_hi_mm","deg_days_cool", 
                "deg_days_heat", "thsw_index", "solar_rad_avg", "solar_energy", "solar_rad_hi", 
                "et"]
        #La finalidad de este FOR soloes recorrer el diccionario clave-valor
        confirmacion=[]
        list_datos_registro=[]
        for clave, valor in k.items():
            dic_datos_registro = {}
            #extraemos el tiempo
            if clave in lista:
                dic_datos_registro[clave]=valor
                list_datos_registro.append(dic_datos_registro)
                confirma = clave in lista
                confirmacion.append(confirma)
            if clave == "ts":
                tiempo_unix= valor
                #print("tiempo unix=", tiempo_unix)
        #print("nueva lista:", list_datos_registro)
        confirmaciones=len(confirmacion) ###para revisar por si hay claves que no se han registrado INT
        #print("------", dic_datos_registro, ", type:", type(dic_datos_registro), ", claves:", len(dic_datos_registro))
        #print("confirmacion:", confirmaciones, type(confirmaciones))
        ## Creamos el JSON objetivo
        diccionario_registro={"pais": 2, "estacion": 1,"lsid":lsid, "time":tiempo_unix, "datos":list_datos_registro}
        #print("----Diccionario:", diccionario_registro)
        return diccionario_registro, "{}-{}".format(confirmaciones, lsid)
        

def formato_json(data_banano, ts_last_BD):
    ### DE AQUI PARA ADELANTE SE UTILIZA EL JSON DE UNA SOLICITUD
    datos = data_banano["sensors"]
    count_G =1
    Id_sensor = []
    data = []
    #print("lo que le llega primer dia:", datos)
    #print("tamaño de datos:", np.shape(datos))
    registros_totales=[]
    claves_encontradas=[]
    ts_inicial=datos[0]["data"][0]["ts"] ##primer tiempo unix de JSON
    nro_Datos_s1=len(datos[0]["data"])

    print("ts_inicial:", ts_inicial)
    print("Numero de datos:", nro_Datos_s1)
    for i in datos: ##para pasar por cada sensor que son 15
        lsid = i["lsid"]
        datos_por_sensor = i["data"]
        unix_ideal=ts_last_BD
        ##extraemnos el ts del sensor 1
        
        sensores_interes= [57386]
        #                      [2       ,3,     5,      9 ,     10,     11,     ,12      ,13,    15]
        """ sensores_interes= [ 267635, 413054]
            #                  [ 9,      10] """

        if lsid in sensores_interes:
            if not datos_por_sensor:
                #CUANDO TODO EL DIA ESTÁ VACIO SE RELLENA CON DATOS NULOS
                #print("Datos de sensor {}({}) vacío".format(count_G,lsid))
                Claves_Registradas_1=[]
                ts_inicial_=ts_inicial
                for k in range(nro_Datos_s1):
                    #print("valor de k:", k)
                    contador, dat=Para_datos_nulos(lsid, ts_inicial_)
                    registros_totales.append(dat)
                    Claves_Registradas_1.append("{}-S{}".format(nro_Datos_s1,count_G))
                    ts_inicial_=ts_inicial_+ 60*60
                claves_encontradas.append(Claves_Registradas_1)
                unix_iteracion=ts_inicial_
                #print("claves 1:", Claves_Registradas_1)
                    #print("rellenando con nullos:", dat)
            else:
                #print("El sensor {}({}) tiene {} registros dentro".format(count_G, lsid, len(datos_por_sensor)))
                #print("--> datos:", datos_por_sensor)
                
                #entramos a cada registro del sensor
                count_Re=1
                diccionario_registro={}
                Claves_Registradas_2=[]
                for k in datos_por_sensor:
                    unix_iteracion = k["ts"]
                    #AQUI TENGO QUE AGREGAR EL WHILE
                    unix_ideal = unix_ideal + 60*60
                    #print("Unix ideal: ", unix_ideal, ", Unix iteracion:", unix_iteracion)
                    while unix_ideal != unix_iteracion:
                        sensor, kr =RellenarConDatosBlanco(lsid,unix_ideal)
                        #print("contador:", sensor)
                        #print("datos:", dat)
                        ###print("datos nulos del sensor {} recuperados".format(sensor))
                        #print("k recuperada :", unix_ideal)
                        diccionario, evaluacion=extra_registros(kr,lsid) ##cada respuesta es un diccionario con los datoss de interes
                        registros_totales.append(diccionario)
                        Claves_Registradas_2.append(evaluacion)
                        unix_ideal = unix_ideal + 60*60
                    
                    diccionario, evaluacion=extra_registros(k,lsid) ##cada respuesta es un diccionario con los datoss de interes
                    registros_totales.append(diccionario)
                    Claves_Registradas_2.append(evaluacion)
                    ###hay que extraer los datos de interés cada iteracion es un diccionario
                            #registros_totales.append(diccionario_registro)
                    count_Re=count_Re+1
                claves_encontradas.append(Claves_Registradas_2)
                print("unix final de dia insertado:", unix_iteracion)
                #print("Claves2:", Claves_Registradas_2)

        count_G=count_G+1
    #print("Diccionarios:", registros_totales)
    #print("claves encontradas:", claves_encontradas, np.shape(claves_encontradas)) #9 sensores, registros extraidos
        #hasta aqui solo repasamos keys que son 4 , lsid, datos, ti_sensor, estructura
    return registros_totales, claves_encontradas, unix_iteracion   

def insert_mongo_many(mydict):
    try:
        cliente = MongoClient(MONGO_URI, serverSelectionTimeoutMS=MONGO_TIEMPO_FUERA)
        #cliente = MongoClient(MONGO_HOST, MONGO_PUERTO)
        baseDatos = cliente[MONGO_BASEDATOS]
        coleccion=baseDatos[MONGO_COLECCION]
        #print("Mydict", mydict, type(mydict))
        x = coleccion.insert_many(mydict)
        #print("ID_",x.inserted_id)
        return "Datos insertado"

    except pymongo.errors.ServerSelectionTimeoutError as errorTiempo:
        return("Teimpo exedido"+ errorTiempo)
    except pymongo.errors.ConnectionFailure as errorConnexion:
        return("Fallo al conectarse a mongodb" + errorConnexion) 

def Datos_menores_24(restante,unix_registro, temp_actual):
    x = unix_registro
    y = unix_registro + restante*60*60
    
    Json_dia = Mensaje_Json(temp_actual, x,y)
    #print("Json dia:", Json_dia)
    ts_last_BD = x
    registros_totales, claves_encontradas, ts_last_BD_retornado =formato_json(Json_dia, ts_last_BD)
    paquetes=restante
    #mydict=lista_json_dia(paquetes,unix_registro,Json_dia)
    R_insert = insert_mongo_many(registros_totales)
    return(R_insert)

def Datos_dias(dias,restante,unix_registro, temp_actual):
    y = unix_registro
    ts_last_BD=unix_registro #el ultimo dato registrado en la BD
    for i in range(dias):
        x = y
        y = x + 86400
        Json_dia = Mensaje_Json(temp_actual, x,y)
        #print("time x: ", x, " time y: ",y)
        #print("json_dia:", Json_dia, "CANTIDAD DE REGISTROS: ",len(Json_dia))
        paquetes=24
        ###################
        registros_totales, claves_encontradas, ts_last_BD_retornado=formato_json(Json_dia,ts_last_BD)
        ts_last_BD=ts_last_BD_retornado
        #ts_vector, ts_inicio=lista_ts(paquetes, ts_inicio)
        #correcto
        """ #print("TS VECTOR", ts_vector,np.shape(ts_vector), "Ts_incio: ",ts_inicio)
        mydict=lista_json_dia(ts_vector,unix_registro,Json_dia)
        print("primer dia:", mydict) """
        #print("Registros totales:", registros_totales)
        R_insert = insert_mongo_many(registros_totales)
        print("Dia {} insertado".format(i+1))
    return(y)

######### funciones para envío de notificaciones a correo de usuarios ####################

def first_name(nombre_usuario):
    if " " in nombre_usuario:
        string_list = nombre_usuario.split()
        name = string_list[0]
    else:
        name = nombre_usuario
    
    return name

def get_dataUser():
    USERS_COLECCION = "users"
    
    try:
        cliente = MongoClient(MONGO_URI, serverSelectionTimeoutMS=MONGO_TIEMPO_FUERA)
        baseDatos = cliente[MONGO_BASEDATOS]
        coleccionUser=baseDatos[USERS_COLECCION]
    
        usuarios_data = []
    
        for x in coleccionUser.find({},{ "_id": 0, "nombres": 1, "email": 1 }):
          # print(x)
          usuarios_data.append(x)
    
        return usuarios_data
    except pymongo.errors.ServerSelectionTimeoutError as errorTiempo:
        return("Tiempo excedido"+ errorTiempo)
    except pymongo.errors.ConnectionFailure as errorConnexion:
        return("Falló al conectarse a mongodb" + errorConnexion) 

def insert_mongo_alert(mydict):
    try:
        cliente = MongoClient(MONGO_URI, serverSelectionTimeoutMS=MONGO_TIEMPO_FUERA)
        #cliente = MongoClient(MONGO_HOST, MONGO_PUERTO)
        baseDatos = cliente[MONGO_BASEDATOS]
        coleccionAlert=baseDatos[ALERT_COLECCION]
        #print("Mydict", mydict, type(mydict))
        x = coleccionAlert.insert_many(mydict)
        # print("ID_",x.inserted_ids)
        return "Datos insertado"

    except pymongo.errors.ServerSelectionTimeoutError as errorTiempo:
        return("Tiempo excedido"+ errorTiempo)
    except pymongo.errors.ConnectionFailure as errorConnexion:
        return("Falló al conectarse a mongodb" + errorConnexion)

def get_item(collection, key):
    for var in collection:
        if key in var:
            value = var[key]
            break
        else:
            value = 0#Este valor es muy bajo, puede quedar ya que nunca va a sobrepasar los límites superiores.
    return value    

def alerta_usuarios(registros_totales):
    # print("lOS REGISTROS SON: ", registros_totales)
    just_data = registros_totales[0]['datos']
    
    #Extracción de los datos necesarios.
    unix_date = registros_totales[0]['time']
    estacion = registros_totales[0]['estacion']
    #Se puede hacer una función que busque cada item y ver si la clave existe y extraer el valor.
    
    temp_avg = get_item(just_data,'temp_out')
    wind_speed_avg = get_item(just_data,'wind_speed_avg')
    # rainfall_mm = just_data[4]['rainfall_mm']
    # et = just_data[6]['et']
    # hum_avg = just_data[3]['hum_out']
    
    # usuarios_data = get_dataUser()
    
    nombre_estacion = dict_estaciones[str(estacion)]
    value_date = datetime.datetime.fromtimestamp(unix_date)
    
    hora =  datetime.datetime.fromtimestamp(unix_date).strftime('%H:%M')

    fecha = value_date.date()
    
    if fecha.month < 10:
        fecha = str(fecha.day)+'/'+str(fecha.month)+'/'+str(fecha.year)
    else:
        fecha = str(fecha.day)+'/'+str(fecha.month)+'/'+str(fecha.year)
    
    temp_cel = round((5/9) * (temp_avg - 32), 2)#Se transforma la temperatura de F a °C
    vel_viento_kmh = round((wind_speed_avg/0.625)*3.6, 2)#Se convierte a km/h
    # evt = round(et*25.4,1)

    print("La temperatura (°C) es : ", temp_cel)
    print("La vel-viento (Km/h) es: ", vel_viento_kmh)
    
    if temp_cel > 35:
        print("La temperatura actual ha sobrepasado el límite de 35 °C")
        
        # Obtener datos de usuarios
        usuarios_data = get_dataUser()

        # # #Mensaje para correo - 1RA FORMA:
        # subject = "Alerta de Temperatura - AHoRa"
        # body = "Hola {nombre}, el siguiente mensaje es para notificarte que la tempertura ha sobrepasado los 35 °C en la estación {estacion_name} en la fecha y hora: {value:%d-%m-%Y %H:%M:%S}."
        
        # message = 'Subject: {}\n\n{}'.format(subject, body)
        
        # context = ssl.create_default_context()
        # with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        #     try:
        #         server.login(from_address, password)
        #         for user in usuarios_data:
        #             user_mail_receiver = user['email']
        #             name_user = first_name(user['nombres'])
        #             server.sendmail(
        #                 from_address,
        #                 user_mail_receiver,
        #                 message.format(nombre=name_user, estacion_name=nombre_estacion, value=value_date).encode('utf-8'))
        #         print("Notificaciones de temperatura enviadas satisfactoriamente")

        #     except:
        #         print("Hubo problemas de envío de notificaciones de temperatura: ", sys.exc_info()[0])

        for user in usuarios_data:
            user_mail_receiver = user['email']
            name_user = first_name(user['nombres'])
            
            message = MIMEMultipart("alternative")
            message["Subject"] = "Alerta de Temperatura - °AHoRa"
            message["From"] = from_address
            message["To"] = user_mail_receiver
            
            html = f"""\
            <html>
            <body>
                <p>Hola {name_user}, el siguiente mensaje es para notificarte que la temperatura ha sobrepasado los 35 °C en la estación {nombre_estacion} el día {fecha} a las {hora} horas.
                </p>
            </body>
            </html>
            """
            # Turn these into plain/html MIMEText objects
            part2 = MIMEText(html, "html")

            # Add HTML/plain-text parts to MIMEMultipart message
            # The email client will try to render the last part first
            message.attach(part2)

            # Enviar correos:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
                try:
                    server.login(from_address, password)
                    server.sendmail(
                        from_address, user_mail_receiver, message.as_string()
                    )
                    print("Notificaciones de velocidad de viento enviadas satisfactoriamente")

                except:
                    print("Hubo problemas de envío de notificaciones de velocidad de viento: ", sys.exc_info()[0])
        
        #Se guarda en la base de datos:
        alerta_dict = [{
                         'estacion': estacion,
                         'nombre_estacion': nombre_estacion,
                         'time': unix_date,
                         'fecha': fecha, 
                         'subject': "temperatura",
                         'intervalo': "hora",
                         'temperatura_c': temp_cel,
                         'unidad': "°C",
                         'mensaje': "La tempertura ha sobrepasado los 35 °C",
                         'hora': hora,
                         'val_for_movil': temp_cel
                      }]
        
        respuesta = insert_mongo_alert(alerta_dict)
        stu_temp = 1
        print("ALERT. TEMPERATURA -> MongoDB: ",respuesta)
        print()
    
    else:
        stu_temp = 0
                
        
    if vel_viento_kmh > 20:
        print("La velocidad del viento actual ha sobrepasado el límite superior de 20 km/h")

        # Obtener datos de usuarios
        usuarios_data = get_dataUser()

        # # #Mensaje para correo - 1RA FORMA:
        # subject = "Alerta de Viento - AHoRa"
        # body = "Hola {nombre}, el siguiente mensaje es para notificarte que la velocidad del viento ha sobrepasado los 20 km/h en la estación {estacion_name} en la fecha y hora: {value:%d-%m-%Y %H:%M:%S}."
        
        # message = 'Subject: {}\n\n{}'.format(subject, body)

        # context = ssl.create_default_context()
        # with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        #     try:
        #         server.login(from_address, password)
        #         for user in usuarios_data:
        #             user_mail_receiver = user['email']
        #             name_user = first_name(user['nombres'])
        #             server.sendmail(
        #                 from_address,
        #                 user_mail_receiver,
        #                 message.format(nombre=name_user, estacion_name=nombre_estacion, value=value_date).encode('utf-8'))
        #         print("Notificaciones de velocidad de viento enviadas satisfactoriamente")

        #     except:
        #         print("Hubo problemas de envío de notificaciones de velocidad de viento: ", sys.exc_info()[0])

        for user in usuarios_data:
            user_mail_receiver = user['email']
            name_user = first_name(user['nombres'])
            
            message = MIMEMultipart("alternative")
            message["Subject"] = "Alerta de Viento - °AHoRa"
            message["From"] = from_address
            message["To"] = user_mail_receiver
            
            html = f"""\
            <html>
            <body>
                <p>Hola {name_user}, el siguiente mensaje es para notificarte que la velocidad del viento ha sobrepasado los 20 km/h en la estación {nombre_estacion} el día {fecha} a las {hora} horas.
                </p>
            </body>
            </html>
            """
            # Turn these into plain/html MIMEText objects
            part2 = MIMEText(html, "html")

            # Add HTML/plain-text parts to MIMEMultipart message
            # The email client will try to render the last part first
            message.attach(part2)

            # Enviar correos:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
                try:
                    server.login(from_address, password)
                    server.sendmail(
                        from_address, user_mail_receiver, message.as_string()
                    )
                    print("Notificaciones de velocidad de viento enviadas satisfactoriamente")

                except:
                    print("Hubo problemas de envío de notificaciones de velocidad de viento: ", sys.exc_info()[0])
        
        #Se guarda en la base de datos:
        alerta_dict = [{
                         'estacion': estacion,
                         'nombre_estacion': nombre_estacion,
                         'time': unix_date,
                         'fecha': fecha,
                         'subject': "vel_viento",
                         'intervalo': "hora",
                         'vel_viento_km_h': vel_viento_kmh,
                         'unidad': "Km/h",
                         'mensaje': "La velocidad del viento ha sobrepasado los 20 km/h",
                         'hora': hora,
                         'val_for_movil': vel_viento_kmh
                      }]
        
        respuesta = insert_mongo_alert(alerta_dict)
        stu_wind = 1
        print("ALERT. VEL_VIENTO -> MongoDB: ",respuesta)
        print()
    
    else:
        stu_wind = 0

    if (stu_temp == 0 and stu_wind == 0):
        response = "-> No fue necesario enviar notificaciones de los parámetros"
    elif (stu_temp == 1 and stu_wind == 0):
        response = "-> Solo se enviaron notificaciones de temperatura"
    elif (stu_temp == 0 and stu_wind == 1):
        response = "-> Solo se enviaron notificaciones de velocidad de viento"
    else:
        response = "-> Se enviaron mensajes de todos los parámetros"
    
    return response

###### CÓDIGO FINAL ##########

# ejecutamos las fechas
temp_actual,x,y = fechas_Inicio_fin()

data_banano = Mensaje_Json(temp_actual,x,y)

#testeamos si existen datos
test_R = test(data_banano)
if test_R=="Nothing":
    print("No hay datos en el Json")
elif test_R == "Data":
    #Ver si el dato ya existe
    result_UR, unix_dato, unix_registro = ultimo_registro(data_banano)
    print(result_UR)
    if result_UR == "New date":
        #insertamos en
        ts_last_BD=unix_registro
        registros_totales, claves_encontradas, ts_last_BD_retornado=formato_json(data_banano, ts_last_BD)
        # respuesta = insert_mongo_many(registros_totales)
        respuesta = alerta_usuarios(registros_totales)
        print(respuesta)
    elif result_UR == "New dateR":
        print("se tienen que recuperar datos")
        # Datos_perdidos=datos_a_recuperar(unix_dato, unix_registro)
        # print("Datos a recuperar:", Datos_perdidos)
        # dias, restante= analisis_recuperacion(Datos_perdidos)
        # print("dias:", dias, " ", "restante:", restante)

        # if dias == 0:

        #     Datos_menores_24_R= Datos_menores_24(restante,unix_registro, temp_actual)
        #     print(Datos_menores_24_R)
            
        # else:
        #     Datos_dias_R= Datos_dias(dias,restante,unix_registro, temp_actual)
        #     unix_registro=int(Datos_dias_R)
        #     Datos_menores_24_R= Datos_menores_24(restante,unix_registro, temp_actual)
        #     print(Datos_menores_24_R)
        #     print("Datos completamente recuperados")
           

    else: 
        #insertamos en
        # ts_last_BD=unix_registro
        # registros_totales, claves_encontradas, ts_last_BD_retornado=formato_json(data_banano, ts_last_BD)
        # respuesta = alerta_usuarios(registros_totales)
        # print(respuesta)
        print("El dato ya existe en la BD")
