#bibliotecas API v2
import collections
import hashlib
import hmac
import time
import ast
import numpy as np
from numpy.core.defchararray import array
#bibliotecas de rquests API
import requests
import json
# import mysql.connector
# from mysql.connector import Error
import datetime
import numpy as np
# import openpyxl
#bibliotecas delta

from datetime import date, timedelta, datetime
import pandas as pd
import json
from pandas import json_normalize

#PARA ENVÍO DE CORREO:
import smtplib, ssl
import sys
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

#Enviar correo a usuarios notificando una alerta
#Dar formato a la etiqueta de estación
dict_estaciones = {"1": "FUNDACIÓN", "2": "OTRAS"}
ALERT_COLECCION = "ALERTAS"
#Crendenciales GMAIL
# from_address = "apis2back@gmail.com"
# password = "fbjtkajygwlxnvbl"
from_address = "servicioaplicativo22@gmail.com"
password = "gibwktbvjyxrahug"

#biblioteca Mongo
import pymongo
from pymongo import MongoClient
from bson.json_util import dumps, loads 
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
cliente = MongoClient(MONGO_URI)
baseDatos = cliente[MONGO_BASEDATOS]
coleccion=baseDatos[MONGO_COLECCION]


def insert_mongo_one(mydict):
    MONGO_BASEDATOS = "PROYECTOC"
    MONGO_COLECCION = "PRETRATAMIENTO"
    cliente = MongoClient(MONGO_URI)
    baseDatos = cliente[MONGO_BASEDATOS]
    coleccion=baseDatos[MONGO_COLECCION]

    try:
        cliente = MongoClient(MONGO_URI, serverSelectionTimeoutMS=MONGO_TIEMPO_FUERA)
        #cliente = MongoClient(MONGO_HOST, MONGO_PUERTO)
        baseDatos = cliente[MONGO_BASEDATOS]
        coleccion=baseDatos[MONGO_COLECCION]
        #print("Mydict", mydict, type(mydict))
        x = coleccion.insert_one(mydict)
        #print("ID_",x.inserted_id)
        return "Dato insertado"

    except pymongo.errors.ServerSelectionTimeoutError as errorTiempo:
        return("Teimpo exedido"+ errorTiempo)
    except pymongo.errors.ConnectionFailure as errorConnexion:
        return("Fallo al conectarse a mongodb" + errorConnexion) 


def consultar(start, end):
    
    try:
        cliente = MongoClient(MONGO_URI, serverSelectionTimeoutMS=MONGO_TIEMPO_FUERA)
        #cliente = MongoClient(MONGO_HOST, MONGO_PUERTO)
        baseDatos = cliente[MONGO_BASEDATOS]
        coleccion=baseDatos[MONGO_COLECCION]
        #solo para 3 datos
        PAQUETE1_SENSOR2 = coleccion.aggregate(
                                        [
                                            {"$match": 
                                                {"$and":
                                                        [
                                                            {"pais":2},
                                                            {"estacion":1},
                                                            {"lsid":57386},
                                                            {"time":{"$gte": start ,"$lt":end}}
                                                        ]
                                                }
                                            },
                                                     
                                            {
                                                "$unwind":"$datos"
                                            },
                                            
                                            {
                                                "$group":
                                                        {
                                                            "_id": "$lsid",
                                                            "Registros_dia":{"$sum":1},
                                                            
                                                            "Hr_D_%" : {"$avg" : "$datos.hum_out"},
                                                            "Hr_max_D_%" : {"$max" : "$datos.hum_out"},
                                                            "Hr_min_D_%" : {"$min" : "$datos.hum_out"},

                                                            "Temperatura_prom" : {"$avg" : "$datos.temp_out"},
                                                            "Temp_min" : {"$min":"$datos.temp_out_lo"},
                                                            "Temp_max" : {"$max" : "$datos.temp_out_hi"},
                                                            "V_viento" : {"$avg" : "$datos.wind_run"},
                                                            "Energia_solar" : {"$sum" : "$datos.solar_energy"},

                                                            "Precipitacion_D" : {"$sum" : "$datos.rainfall_mm"},
                                                            "Tasa_lluvia_D" : {"$avg" : "$datos.rain_rate_hi_mm"},
                                                            "ET" : {"$sum" : "$datos.et"}
                                                        
                                                        }
                                            },
                                            
                                            {
                                                "$addFields":
                                                            {
                                                                "Temperatura_D" : {"$round":[{"$multiply" : [{"$subtract" : ["$Temperatura_prom",32]}, 5/9]},2]},
                                                                "Temp_min_D": {"$round":[{"$multiply" : [{"$subtract" : ["$Temp_min",32]}, 5/9]},2]},
                                                                "Temp_max_D": {"$round":[{"$multiply" : [{"$subtract" : ["$Temp_max",32]}, 5/9]},2]},
                                                                "V_viento_D":{"$round":[{"$divide" : ["$V_viento", 0.625]},2]},
                                                                "Energia_solar_D": {"$round":[{"$multiply":["$Energia_solar", 0.04184]}, 2]},
                                                                "ET_D": {"$round":[ {"$multiply":["$ET", 25.4]},1]}
                                                            }
                                            },
                                            {
                                                "$project":{
                                                    "_id":0,
                                                    "Temperatura_D":1,
                                                    "Temp_min_D":1,
                                                    "Temp_max_D":1,
                                                    "Energia_solar_D":1,
                                                    "ET_D":1,
                                                    "Precipitacion_D":1,
                                                    "Tasa_lluvia_D":1,
                                                    "Hr_D_%":1,
                                                    "Hr_max_D_%":1,
                                                    "Hr_min_D_%":1,
                                                    "V_viento_D":1,
                                                    "Registros_dia":1,
                                                    
                                                }
                                            }
                                            
                                
                                        ]
                                    )
        PAQUETE2_SENSOR2 = coleccion.aggregate(
                                        [
                                            {"$match": 
                                                {"$and":
                                                        [
                                                            {"pais":2},
                                                            {"estacion":1},
                                                            {"lsid":57386},
                                                            {"time":{"$gte": start ,"$lt":end}}
                                                        ]
                                                }
                                            },
                                            {
                                                "$unwind":"$datos"
                                            },
                                            {
                                                "$match": {"datos.temp_out":{"$exists":"true"}}
                                            },
                                            {
                                                "$addFields":{
                                                    "ajuste":{
                                                        "$cond":{
                                                            "if":{"$gt":["$datos.temp_out",91.4]},
                                                            "then":91.4,
                                                            "else":{
                                                                "$cond":{
                                                                    "if":{"$lt":["$datos.temp_out",55.4]},
                                                                    "then":55.4,
                                                                    "else":"$datos.temp_out"
                                                                }
                                                            }
                                                        }
                                                    }
                                                }
                                            },
                                            {
                                                "$group":{
                                                    "_id":"lsid",
                                                    "contador":{"$sum":1},
                                                    "temp_ajust_avg":{"$avg":"$ajuste"}
                                                }
                                            },
                                            {
                                                "$addFields":{
                                                    "GDD_D":{"$subtract":[{"$multiply" : [{"$subtract" : ["$temp_ajust_avg",32]}, 5/9]},13]}
                                                    
                                                }
                                            },
                                            {
                                                "$project":{
                                                    "_id":0,
                                                    "contador":1,
                                                    "GDD_D":1
                                                }
                                            }
                                            
                                        ]
                                    )
        Datos2= coleccion.aggregate(
                                        [
                                            {"$match": 
                                                        {"$and":
                                                                [
                                                                    {"pais":2},
                                                                    {"estacion":1},
                                                                    {"lsid":57386},
                                                                    {"time":{"$gte": start ,"$lt":end}}
                                                                ]
                                                        }
                                            },
                                            {
                                                "$project":{"_id":0,"lsid":1,"time":1,"datos":1}
                                            }
                                        ]
                                    )
        #la siguiente consulta es para extraer todos los datos de mongo
        #Datos = coleccion.aggregate([{"$match":{"time":{"$gte": start ,"$lt":end}}}, {"$group":{"_id":"$lsid", "repetidos":{"$sum":1}, "suma_bar":{"$sum":"$datos.moist_soil_last"}}}])
        #Datos = coleccion.find({"time":{"$gte": start ,"$lt":end}})
        ## PARA UN SOLO SENSOR

        #Datos=coleccion.aggregate([{"$group":{"_id":"$lsid"}}])
        return(PAQUETE1_SENSOR2,PAQUETE2_SENSOR2, Datos2)

    except pymongo.errors.ServerSelectionTimeoutError as errorTiempo:
        return("Tiempo exedido"+ errorTiempo)
    except pymongo.errors.ConnectionFailure as errorConnexion:
        return("Fallo al conectarse a mongodb" + errorConnexion) 

def consultar_last_date(today):
    MONGO_BASEDATOS = "PROYECTOC"
    MONGO_COLECCION = "PRETRATAMIENTO"
    cliente = MongoClient(MONGO_URI)
    baseDatos = cliente[MONGO_BASEDATOS]
    coleccion=baseDatos[MONGO_COLECCION]
    
    ##extraemos el tiempo del ultimo registro insertado
    try:
        cliente = MongoClient(MONGO_URI, serverSelectionTimeoutMS=MONGO_TIEMPO_FUERA)
        #cliente = MongoClient(MONGO_HOST, MONGO_PUERTO)
        baseDatos = cliente[MONGO_BASEDATOS]
        coleccion=baseDatos[MONGO_COLECCION]
        cursor_UR = coleccion.find().limit(1).sort([("$natural", -1)])
        json_cursor_UR = list(cursor_UR)[0]
        unix_registro = str(json_cursor_UR["Fecha_D_str"])
        #lo convertimos a formato date
        fec = datetime.strptime(unix_registro, '%d/%m/%Y')
        #nos quedamos con el dia
        fec_date=fec.date()
        print("fec:", fec_date, type(fec_date))
        dias_restantes = (today-fec_date).days 
        if dias_restantes > 1:
            return(dias_restantes, fec_date)

        elif dias_restantes==1:
            return(dias_restantes, fec_date)

    except pymongo.errors.ServerSelectionTimeoutError as errorTiempo:
        return("Teimpo exedido"+ errorTiempo)
    except pymongo.errors.ConnectionFailure as errorConnexion:
        return("Fallo al conectarse a mongodb" + errorConnexion)
#Todos los sensores ordenados segun el JSON
#lsid = [264588, 264589, 267629, 264590, 267630, 267689, 264597, 264599, 267635, 413054, 413052, 413053, 264600, 264601, 264602]
#Sensor=[   1,     2,      3,      4,      5,      6,      7,      8,      9,      10,     11,     12,     13,     14,     15  ]

#Orden mostrado en weatherlink
#Sensor=[   2,      3,      15,     5,      9,      13,     11,     12,     10]
#cantidad=[ 38,     16,     4,      4,      4,      16,     4,      4,      4]

############ FUNCIONES PARA ENVÍO DE CORREO ###################

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
        return("Fallo al conectarse a mongodb" + errorConnexion) 

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
        return("Teimpo exedido"+ errorTiempo)
    except pymongo.errors.ConnectionFailure as errorConnexion:
        return("Fallo al conectarse a mongodb" + errorConnexion)

def alerta_usuarios(Datos_dia):
    # print("lOS REGISTROS SON: ", Datos_dia)
    just_data = Datos_dia['Datos']
    
    #Extracción de los datos necesarios.
    unix_date = Datos_dia['Fecha_D']
    str_date = Datos_dia['Fecha_D_str']
    estacion = Datos_dia['estacion']
    #Se puede hacer una función que busque cada item y ver si la clave existe y extraer el valor.

    rainfall_mm = just_data['Precipitacion_D']
    evt_mm = just_data['ET_D']
    hum_avg = round(just_data['Hr_D_%'], 2)
    temp_cel = just_data['Temperatura_D']
    vel_viento_kmh = just_data['V_viento_D']
    
    # usuarios_data = get_dataUser()
    
    nombre_estacion = dict_estaciones[str(estacion)]
    # value_date = datetime.fromtimestamp(unix_date)
    
    if temp_cel > 35:
        print("La temperatura promedio del día ha sobrepasado el límite de 35 °C")
        
        # Obtener datos de usuarios:
        usuarios_data = get_dataUser()

        # PRIMERA FORMA ENVÍO CORREOS:
        # Mensaje para correo
        # subject = "Alerta de Temperatura - AHoRa"
        # body = "Hola {nombre}, el siguiente mensaje es para notificarte que la tempertura promedio diaria ha sobrepasado los 35 °C en la estación {estacion_name} en la fecha: {value}."
        
        # # message = "Subject:" + subject + "\n" + body
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
        #                 message.format(nombre=name_user, estacion_name=nombre_estacion, value=str_date).encode('utf-8'))
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
                <p>Hola {name_user}, el siguiente mensaje es para notificarte que la tempertura promedio diaria ha sobrepasado los 35 °C en la estación {nombre_estacion} el la fecha {str_date}.
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
                    print("Notificaciones de temperatura enviadas satisfactoriamente")

                except:
                    print("Hubo problemas de envío de notificaciones de temperatura: ", sys.exc_info()[0])
        
        
        #Se guarda en la base de datos:
        alerta_dict = [{
                         'estacion': estacion,
                         'nombre_estacion': nombre_estacion,
                         'time': unix_date,
                         'fecha': str_date, 
                         'subject': "temperatura",
                         'intervalo': "dia",
                         'temperatura_c': temp_cel,
                         'unidad': "°C",
                         'mensaje': "La tempertura ha sobrepasado los 35 °C",
                         'val_for_movil': temp_cel
                      }]
        
        respuesta = insert_mongo_alert(alerta_dict)
        print("ALERT. TEMPERATURA -> MongoDB: ",respuesta)
        print()
                
        
    if vel_viento_kmh > 20:
        print("La velocidad del viento promedio en el día ha sobrepasado el límite superior de 20 km/h")

        # Obtener datos de usuarios:
        usuarios_data = get_dataUser()

        #1RA FORMA DE ENVÍO DE CORREOS:
        # #Mensaje para correo
        # subject = "Alerta de Viento - AHoRa"
        # body = "Hola {nombre}, el siguiente mensaje es para notificarte que la velocidad del viento promedio diaria ha sobrepasado los 20 km/h en la estación {estacion_name} en la fecha: {value}."
        
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
        #                 message.format(nombre=name_user, estacion_name=nombre_estacion, value=str_date).encode('utf-8'))
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
                <p>Hola {name_user}, el siguiente mensaje es para notificarte que la velocidad del viento promedio diaria ha sobrepasado los 20 km/h en la estación {nombre_estacion} el día {str_date}.
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
                         'fecha': str_date,
                         'subject': "vel_viento",
                         'intervalo': "dia",
                         'vel_viento_km_h': vel_viento_kmh,
                         'unidad': "Km/h",
                         'mensaje': "La velocidad del viento ha sobrepasado los 20 km/h",
                         'val_for_movil': vel_viento_kmh
                      }]
        
        respuesta = insert_mongo_alert(alerta_dict)
        print("ALERT. VEL_VIENTO -> MongoDB: ",respuesta)
        print()
    
    if rainfall_mm > 60:
        print("La precipitación diaria a sobrepasado el límite de 60 mm/día")
        
        # Obtener datos de usuarios:
        usuarios_data = get_dataUser()
        
        # #PRIMERA FORMA ENVÍO DE CORREOS:
        # #Mensaje para correo
        # subject = "Alerta de Precipitación Diaria - AHoRa"
        # body = "Hola {nombre}, el siguiente mensaje es para notificarte que la precipitación del día ha sobrepasado los 60 mm/día en la estación {estacion_name} en la fecha: {value}."
        
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
        #                 message.format(nombre=name_user, estacion_name=nombre_estacion, value=str_date).encode('utf-8'))
        #         print("Notificaciones de precipitación diaria enviadas satisfactoriamente")

        #     except:
        #         print("Hubo problemas de envío de notificaciones de precipitación diaria: ", sys.exc_info()[0])
        
        for user in usuarios_data:
            user_mail_receiver = user['email']
            name_user = first_name(user['nombres'])
            
            message = MIMEMultipart("alternative")
            message["Subject"] = "Alerta de Precipitación Diaria - °AHoRa"
            message["From"] = from_address
            message["To"] = user_mail_receiver
            
            html = f"""\
            <html>
            <body>
                <p>Hola {name_user}, el siguiente mensaje es para notificarte que la precipitación del día ha sobrepasado los 60 mm/día en la estación {nombre_estacion} el día {str_date}.
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
                    print("Notificaciones de precipitación diaria enviadas satisfactoriamente")

                except:
                    print("Hubo problemas de envío de notificaciones de precipitación diaria: ", sys.exc_info()[0])
        

        #Se guarda en la base de datos:
        alerta_dict = [{
                         'estacion': estacion,
                         'nombre_estacion': nombre_estacion,
                         'time': unix_date,
                         'fecha': str_date,
                         'subject': "precipitacion_D",
                         'intervalo': "dia",
                         'precipitacion_mm_D': rainfall_mm,
                         'unidad': "mm",
                         'mensaje': "La precipitación del día ha sobrepasado los 60 mm/día",
                         'val_for_movil': rainfall_mm
                      }]
        
        respuesta = insert_mongo_alert(alerta_dict)
        print("ALERT. PRECIPITACION DIARIA -> MongoDB: ",respuesta)
                    
    
    if hum_avg > 80:
        print("La humedad relativa del día ha sobrepasado el 80%")

        # Obtener datos de usuarios:
        usuarios_data = get_dataUser()
        
        # # PRIMERA FORMA ENVÍO DE CORREOS:
        # #Mensaje para correo
        # subject = "Alerta de Humedad - AHoRa"
        # body = "Hola {nombre}, el siguiente mensaje es para notificarte que la humedad relativa promedio diaria sobrepasó el 80% en la estación {estacion_name} en la fecha: {value}. Indica un posible riesgo de sigatoka."
        
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
        #                 message.format(nombre=name_user, estacion_name=nombre_estacion, value=str_date).encode('utf-8'))
        #         print("Notificaciones de humedad relativa diaria enviadas satisfactoriamente")

        #     except:
        #         print("Hubo problemas de envío de notificaciones de humedad relativa diaria: ", sys.exc_info()[0])

        for user in usuarios_data:
            user_mail_receiver = user['email']
            name_user = first_name(user['nombres'])
            
            message = MIMEMultipart("alternative")
            message["Subject"] = "Alerta de Humedad - °AHoRa"
            message["From"] = from_address
            message["To"] = user_mail_receiver
            
            html = f"""\
            <html>
            <body>
                <p>Hola {name_user}, el siguiente mensaje es para notificarte que la humedad relativa promedio diaria sobrepasó el 80% en la estación {nombre_estacion} el día {str_date}.
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
                    print("Notificaciones de humedad relativa diaria enviadas satisfactoriamente")

                except:
                    print("Hubo problemas de envío de notificaciones de humedad relativa diaria: ", sys.exc_info()[0])
        
        #Se guarda en la base de datos:
        alerta_dict = [{
                         'estacion': estacion,
                         'nombre_estacion': nombre_estacion,
                         'time': unix_date,  
                         'fecha': str_date, 
                         'subject': "humedad_D",
                         'intervalo': "dia",
                         'humedad_avg_porcent': hum_avg,
                         'unidad': "%",
                         'mensaje': "La humedad relativa promedio del día sobrepasó el 80%",
                         'val_for_movil': hum_avg
                      }]
        
        respuesta = insert_mongo_alert(alerta_dict)
        print("ALERT. HUMEDAD DIARIA -> MongoDB: ",respuesta)
    
    
    # if rainfall_mm <= evt_mm/2:
    #     # print("La temperatura ha sobrepasado el límite de X °C")
    #     usuarios_data = get_dataUser()
    #     message = """Subject: Alerta de Temperatura - °AHoRa

    #     Hola {nombre}, el siguiente mensaje es para notificarte que la lectura de precipitación es la mitad de la evapotranspiración en la estación {estacion_name} en la fecha: {value}. Hay deficit de agua y por tanto se debe regar"""
        
    #     # for user in usuarios_data:
    #     #     # user_mail_receiver = user['email']
    #     #     name_user = first_name(user['nombres'])
    #     #     print(message.format(nombre=name_user, estacion_name=nombre_estacion, value=value_date))
        
    #     context = ssl.create_default_context()
    #     with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
    #         try:
    #             server.login(from_address, password)
    #             for user in usuarios_data:
    #                 user_mail_receiver = user['email']
    #                 name_user = first_name(user['nombres'])
    #                 server.sendmail(
    #                     from_address,
    #                     user_mail_receiver,
    #                     message.format(nombre=name_user, estacion_name=nombre_estacion, value=str_date).encode('utf-8'))
    #             print("Notificaciones de precipitación menor que evapotranspiración enviadas satisfactoriamente")

    #         except:
    #             print("Hubo problemas de envío de notificaciones de precipitación menor que evapotranspiración: ", sys.exc_info()[0])
            
    #     #Se guarda en la base de datos:
    #     alerta_dict = [{
    #                       'estacion': estacion,
    #                       'time': unix_date, 
    #                       'fecha': str_date,
    #                       'subject': "precipitacion_baja",
    #                       'precipit_mm': rainfall_mm,
    #                       'evt_mm': evt_mm,
    #                       'mensaje': "la precipitación es la mitad de la evapotranspiración"
    #                   }]
        
    #     respuesta = insert_mongo_alert(alerta_dict)
    #     print("ALERT. PRECIP. BAJA -> MongoDB: ",respuesta)
    
    # if rainfall_mm >= evt_mm*2:
    #     # print("La temperatura ha sobrepasado el límite de X °C")
    #     usuarios_data = get_dataUser()
    #     message = """Subject: Alerta de Temperatura - °AHoRa

    #     Hola {nombre}, el siguiente mensaje es para notificarte que la le lectura de precipitación es el doble de la evapotranspiración en la estación {estacion_name} en la fecha: {value}. Hay exceso de agua y por tanto se debe tener canales de drenaje"""
        
    #     # for user in usuarios_data:
    #     #     # user_mail_receiver = user['email']
    #     #     name_user = first_name(user['nombres'])
    #     #     print(message.format(nombre=name_user, estacion_name=nombre_estacion, value=str_date))
        
    #     context = ssl.create_default_context()
    #     with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
    #         try:
    #             server.login(from_address, password)
    #             for user in usuarios_data:
    #                 user_mail_receiver = user['email']
    #                 name_user = first_name(user['nombres'])
    #                 server.sendmail(
    #                     from_address,
    #                     user_mail_receiver,
    #                     message.format(nombre=name_user, estacion_name=nombre_estacion, value=str_date).encode('utf-8'))
    #             print("Notificaciones de precipitación mayor que evapotranspiración enviadas satisfactoriamente")

    #         except:
    #             print("Hubo problemas de envío de notificaciones de precipitación mayor que evapotranspiración: ", sys.exc_info()[0])
        
    #     #Se guarda en la base de datos:
    #     alerta_dict = [{
    #                       'estacion': estacion,
    #                       'time': unix_date,  
    #                       'fecha': str_date,
    #                       'subject': "precipitacion_alta",
    #                       'precipit_mm': rainfall_mm,
    #                       'evt_mm': evt_mm,
    #                       'mensaje': "la precipitación es es el doble de la evapotranspiración"
    #                   }]
        
    #     respuesta = insert_mongo_alert(alerta_dict)
    #     print("ALERT. PRECIP. ALTA -> MongoDB: ",respuesta)
    
    response = "Código de envío de correos de alerta ejecutado"
    
    return response

################ CÓDIGO FINAL #################
## Fecha actual
today = date.today()
print("today:", today, type(today))
Ultima_fecha_BD, fec_date = consultar_last_date(today)
if Ultima_fecha_BD==1:
    print("la BD está actualizada")
else:
    fecha_inicio=fec_date
    print("fecha ultima en BD 1:", fecha_inicio)
    fecha_inicio=fecha_inicio+timedelta(1) #sumamos 1 dia para que no empiece desde el dia de registro- no se duplique
    print("A partir de aqui se actualizará:", fecha_inicio)
    #convertimos dicha fecha a unix
    start= int(time.mktime(fecha_inicio.timetuple()))
    end = start + 86400
    for k in range(Ultima_fecha_BD-1): #restamos uno para que no se considere la fecha actual

        PAQUETE1_SENSOR2, PAQUETE2_SENSOR2, Datos2 = consultar(start, end)
        ##corroboracion de datos 
        PAQUETE1_SENSOR2=list(PAQUETE1_SENSOR2)
        PAQUETE2_SENSOR2=list(PAQUETE2_SENSOR2)
        #
        #print("datos crudos:", list(Datos2))
        #EXTRAEMOS EL DIA 
        Fecha_completa=datetime.fromtimestamp(start)




        fecha=Fecha_completa.date()
        if fecha.month < 10:
            fecha = str(fecha.day)+'/'+str(fecha.month)+'/'+str(fecha.year)
        else:
            fecha = str(fecha.day)+'/'+str(fecha.month)+'/'+str(fecha.year)

        print("fecha:",fecha, "formato unix:", start)

        #ARMAMOS UN NUEVO DICCIONARIO
        Datos_dia ={}
        union_registros={}
        union_registros.update(PAQUETE1_SENSOR2[0])
        union_registros.update(PAQUETE2_SENSOR2[0])
        print("Union de registros:", union_registros)

        Datos_dia["pais"]=2
        Datos_dia["estacion"]=1
        Datos_dia["Fecha_D"] =start
        Datos_dia["Fecha_D_str"]=fecha
        Datos_dia["Datos"]=union_registros

        # respuesta = insert_mongo_one(Datos_dia)
        respuesta = alerta_usuarios(Datos_dia)
        print(respuesta)
        start = end
        end = start + 86400
        print("iteracion {} de {} insertado".format(k, Ultima_fecha_BD))
        print("")
