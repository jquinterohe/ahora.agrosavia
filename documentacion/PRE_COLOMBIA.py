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
import datetime
import numpy as np
import openpyxl
#bibliotecas delta

from datetime import date, timedelta, datetime
import pandas as pd
import json

#biblioteca Mongo
import pymongo
from pymongo import MongoClient
from bson.json_util import dumps, loads 

MONGO_HOST = "127.0.0.1"
MONGO_PUERTO ="27017"
MONGO_PWD = "ciba1515323232"
MONGO_USER = "root"
MONGO_TIEMPO_FUERA =10000
MONGO_BASEDATOS = "PROYECTO"
MONGO_COLECCION = "ESTACIONES"

MONGO_URI = "mongodb://"+ MONGO_USER +":"+ MONGO_PWD + "@"+MONGO_HOST +":" + MONGO_PUERTO + "/"
#+ MONGO_BASEDATOS 

cliente = MongoClient(MONGO_URI)
baseDatos = cliente[MONGO_BASEDATOS]
coleccion=baseDatos[MONGO_COLECCION]

pais = 2
estacion_name =     {"1": "FUNDACIÓN"}
estacion_lsid =       {"1": 57386}


def PRETRATAMIENTO(pais, estacion, lsid):

    def insert_mongo_one(mydict):
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
                                                                {"pais":pais},
                                                                {"estacion":estacion},
                                                                {"lsid":lsid},
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
                                                                {"pais":pais},
                                                                {"estacion":estacion},
                                                                {"lsid":lsid},
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
                                                                        {"pais":pais},
                                                                        {"estacion":estacion},
                                                                        {"lsid":lsid},
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
            cursor_UR = coleccion.find({"pais":pais, "estacion":estacion}).limit(1).sort([("$natural", -1)])
            json_cursor_UR = list(cursor_UR)[0]
            print("CURSOR:", json_cursor_UR)
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
                fecha = str(fecha.day)+'/0'+str(fecha.month)+'/'+str(fecha.year)
            else:
                fecha = str(fecha.day)+'/'+str(fecha.month)+'/'+str(fecha.year)

            print("fecha:",fecha, "formato unix:", start)

            #ARMAMOS UN NUEVO DICCIONARIO
            Datos_dia ={}
            union_registros={}
            union_registros.update(PAQUETE1_SENSOR2[0])
            union_registros.update(PAQUETE2_SENSOR2[0])
            print("Union de registros:", union_registros)

            Datos_dia["pais"]=pais
            Datos_dia["estacion"]=estacion
            Datos_dia["Fecha_D"] =start
            Datos_dia["Fecha_D_str"]=fecha
            Datos_dia["Datos"]=union_registros

            respuesta = insert_mongo_one(Datos_dia)
            print(respuesta)
            start = end
            end = start + 86400
            print("iteracion {} de {} insertado".format(k, Ultima_fecha_BD))
            print("")

print("tamaño de estaciones:", len(estacion_name))

for i in range(len(estacion_name)):
    i=i+ 1
    estacion = i
    Name = estacion_name["{}".format(i)]
    lsid = estacion_lsid["{}".format(i)]

    PRETRA_= PRETRATAMIENTO(pais, estacion, lsid)
    print(" ESTACION '{}' -- PRETRATAMIENTO EN '{}' EJECUTADO CORRECTAMENTE". format(i, Name))
    print("____________________________________")



