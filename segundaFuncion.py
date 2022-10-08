import pymysql
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from datetime import date
#biblioteca Mongo
import pymongo
from pymongo import MongoClient
from bson.json_util import dumps, loads
import time
import math

from App import MONGO_HOST, MONGO_PUERTO, MONGO_PWD, MONGO_USER, MONGO_TIEMPO_FUERA, MONGO_BASEDATOS
MONGO_COLECCION = "PRETRATAMIENTO"

MONGO_URI = "mongodb://"+ MONGO_USER +":"+ MONGO_PWD + "@"+MONGO_HOST +":" + MONGO_PUERTO + "/"+ MONGO_BASEDATOS


def convert_formato_fecha(fec):
    fec = datetime.strptime(fec, '%d/%m/%Y')
    #restamos 1 dia que es el de consulta
    fec =fec -timedelta(1)
    fec_unix=int(time.mktime(fec.timetuple()))
    if fec.month < 10:
        fec = str(fec.day)+'/0'+str(fec.month)+'/'+str(fec.year)
    else:
        fec = str(fec.day)+'/'+str(fec.month)+'/'+str(fec.year)
        
    return(fec, fec_unix)

def convert_formato_fecha_forward(fec):
    fec = datetime.strptime(fec, '%d/%m/%Y')
    ## CONVERTIMOS A FORMATO UNIX
    fec_unix=int(time.mktime(fec.timetuple()))
    if fec.month < 10:
        fec = str(fec.day)+'/0'+str(fec.month)+'/'+str(fec.year)
    else:
        fec = str(fec.day)+'/'+str(fec.month)+'/'+str(fec.year)
        
    return(fec, fec_unix)

def BD_MONGO_BACWARD(pais, estacion, fec_unix_usuario): ###regresa valores menores e iguales que fecha de consulta -1
    
    try:
        cliente = MongoClient(MONGO_URI, serverSelectionTimeoutMS=MONGO_TIEMPO_FUERA)
        baseDatos = cliente[MONGO_BASEDATOS]
        coleccion=baseDatos[MONGO_COLECCION]
        ##4 CONSULTAS A LA VEZ
        datos_mongo = coleccion.aggregate(
                                        [
                                            {"$match": 
                                                {"$and":
                                                        [
                                                            {"pais":pais},
                                                            {"estacion":estacion},
                                                            {"Fecha_D":{"$lte": fec_unix_usuario}}
                                                        ]
                                                }
                                            },
                                            {
                                            "$project":{
                                                "_id":0,
                                                "Fecha_D_str":1,
                                                "Datos.Temperatura_D":1,
                                                "Datos.GDD_D":1
                                            }
                                            }
                                        ])
        datos_ = list(datos_mongo)
                
        return datos_
    except pymongo.errors.ServerSelectionTimeoutError as errorTiempo:
        return("Teimpo exedido"+ errorTiempo)
    except pymongo.errors.ConnectionFailure as errorConnexion:
        return("Fallo al conectarse a mongodb" + errorConnexion)

def BD_MONGO_FORWARD(pais, estacion, fec_unix_usuario): ###regresa valores menores e iguales que fecha de consulta -1
    
    try:
        cliente = MongoClient(MONGO_URI, serverSelectionTimeoutMS=MONGO_TIEMPO_FUERA)
        baseDatos = cliente[MONGO_BASEDATOS]
        coleccion=baseDatos[MONGO_COLECCION]
        ##4 CONSULTAS A LA VEZ
        datos_mongo = coleccion.aggregate(
                                        [
                                            {"$match": 
                                                {"$and":
                                                        [
                                                            {"pais":pais},
                                                            {"estacion":estacion},
                                                            {"Fecha_D":{"$gte": fec_unix_usuario}}
                                                        ]
                                                }
                                            },
                                            {
                                            "$project":{
                                                "_id":0,
                                                "Fecha_D_str":1,
                                                "Datos.Temperatura_D":1,
                                                "Datos.GDD_D":1,
                                                "Datos.Hr_D_%":1
                                            }
                                            }
                                        ])
        datos_ = list(datos_mongo)
                
        return datos_
    except pymongo.errors.ServerSelectionTimeoutError as errorTiempo:
        return("Teimpo exedido"+ errorTiempo)
    except pymongo.errors.ConnectionFailure as errorConnexion:
        return("Fallo al conectarse a mongodb" + errorConnexion)

def EstimacionFechaFloracion(fec, estacion):
    pais = 2#1 peru
    print("Fecha ingresada por el usuario:", fec)
    #convertimos a string y unix y restamos el dia de consulta
    fec_string_usuario, fec_unix_usuario = convert_formato_fecha(fec)
    print("Fecha a ingresar a calculo:", fec_string_usuario)
    ##solicitamos datos
    datos = BD_MONGO_BACWARD(pais, estacion, fec_unix_usuario)

    #####iniciamos los calculos
    ##invertir lista
    datos_new = list(reversed(datos))
    Vector_datos=[]
    GDA_acum = 0
    vector_temp = []
    vector_gda = []
    vector_fecha = []
    GDA_ACUMULADO = 0
    for k in datos_new:
        gdd = k["Datos"]["GDD_D"]
        GDA_acum += gdd
        fecha = k["Fecha_D_str"]
        temperatura = k["Datos"]["Temperatura_D"]

        vector_temp.append(temperatura)
        vector_gda.append(gdd)
        vector_fecha.append(fecha)

        #print("valor de k1:", k, "sumatoria:", GDA_acum)
        if GDA_acum >= 900:
            break
    #### re invertimos los datos para que las fechas esten en ascendente
    vector_fecha=list(reversed(vector_fecha))
    vector_temp=list(reversed(vector_temp))
    vector_gda=list(reversed(vector_gda))
    for k in range(len(vector_fecha)):
        GDA_ACUMULADO += vector_gda[k]
        Vector_datos.append((vector_fecha[k], round(vector_temp[k],2), round(GDA_ACUMULADO,2)))
    nSemanas=round((len(Vector_datos))/7, 1)
    return round(GDA_acum,1), fecha, nSemanas , Vector_datos


def EstimacionFechaCosecha(fec, estacion):
    pais = 2#1 peru
    print("Fecha ingresada por el usuario:", fec)
    #convertimos a string y unix y restamos el dia de consulta
    fec_string_usuario, fec_unix_usuario = convert_formato_fecha_forward(fec)
    print("Fecha a ingresar a calculo:", fec_string_usuario)
    ##solicitamos datos
    datos = BD_MONGO_FORWARD(pais, estacion, fec_unix_usuario)

    Vector_datos=[]
    GDA_acum = 0
    TEMP_acum = 0
    HUM_acum = 0
    gdd = 0 
    for k in datos:
        gdd = k["Datos"]["GDD_D"]
        GDA_acum += gdd
        fecha = k["Fecha_D_str"]
        humedad = k["Datos"]["Hr_D_%"]
        HUM_acum += humedad
        temperatura = k["Datos"]["Temperatura_D"]
        TEMP_acum += temperatura
        Vector_datos.append((fecha, round(temperatura,2), round(GDA_acum,2), round(humedad,2)))
        if GDA_acum >= 900:
            break#print("valor de k1:", k, "sumatoria:", GDA_acum)
    #
    if GDA_acum <900:
        GDA_DATOS_REALES=GDA_acum
        datos_tomados=int(len(Vector_datos)) #dias tomados en cuenta
        temp_promedio = TEMP_acum/datos_tomados
        hum_promedio = HUM_acum/datos_tomados
        gda_promedio = GDA_acum/datos_tomados
        gda_Restantes = 900-GDA_acum
        estimacion = math.ceil(gda_Restantes/gda_promedio)
        print("estimacion:", estimacion)
        #estimacion = int(round(gda_Restantes/gda_promedio))
        """ print("promedio de gdd:", gda_promedio)
        print("promedio de humedad:", hum_promedio)
        print("Gda acumulados:", GDA_acum, " GDA restantes:", gda_Restantes)
        print("Estimacion:", estimacion) """
        #rellenamos los datos que faltan para la cosecha
        Vector_datos2=[]
        for k in range(int(estimacion)):
            GDA_acum += gda_promedio
            fec=datetime.strptime(fec_string_usuario, "%d/%m/%Y") #convertimos a date
            fecha_next = fec + timedelta(datos_tomados+k)
            fecha_next = fecha_next.strftime("%d/%m/%Y")
            Vector_datos2.append((fecha_next,"--", round(temp_promedio,2),"--", round(GDA_acum,2),"--", round(hum_promedio,2)))

        nSemanas=round((len(Vector_datos))/7, 1)
        fec_final = fecha_next
        return round(GDA_DATOS_REALES,1), fec_string_usuario, fec_final, estimacion, Vector_datos, nSemanas, round(temp_promedio, 2)
    else:
        datos_tomados=int(len(Vector_datos)) #dias tomados en cuenta
        #print("cantidad de datos:", datos_tomados)
        temp_promedio = TEMP_acum/datos_tomados
        nSemanas=round((len(Vector_datos))/7, 1)
        estimacion=0
        fec_final = fecha
        return round(GDA_acum,1), fec_string_usuario, fec_final, estimacion, Vector_datos, nSemanas, round(temp_promedio, 2)


def EstimacionNroHojasHijo(fec, estacion):
    pais = 2 #2 colombia
    #convertimos a string y unix y restamos el dia de consulta
    fec_string_usuario, fec_unix_usuario = convert_formato_fecha_forward(fec)
    ##solicitamos datos
    datos = BD_MONGO_FORWARD(pais, estacion, fec_unix_usuario)
    Vector_datos=[]
    GDA_acum = 0
    TEMP_acum = 0
    HUM_acum = 0
    GDA = 0
    gdd = 0
    for k in datos:
        gdd = k["Datos"]["GDD_D"]
        GDA_acum += gdd
        fecha = k["Fecha_D_str"]
        humedad = k["Datos"]["Hr_D_%"]
        HUM_acum += humedad
        temperatura = k["Datos"]["Temperatura_D"]
        TEMP_acum += temperatura
        Vector_datos.append((fecha, round(temperatura,2), round(gdd,2)))
        if GDA_acum >= 900:
            break 
    if GDA_acum <900:
        GDA_DATOS_REALES=GDA_acum
        datos_tomados=int(len(Vector_datos)) #dias tomados en cuenta
        nHojas = GDA_DATOS_REALES/108
        nSemanas=round((len(Vector_datos))/7, 1)
        #fec_final = fecha_next
        opcion=1
        return round(nHojas,1), Vector_datos
    else:
        datos_tomados=int(len(Vector_datos)) #dias tomados en cuenta
        nHojas = GDA_acum/108
        opcion=2
        return round(nHojas,1), Vector_datos


##consulta para graficas de datos actuales de una semana

def BD_MONGO_DATOS(pais, estacion, fec_unix_usuario): ###regresa valores menores e iguales que fecha de consulta -1
    MONGO_COLECCION = "PRETRATAMIENTO"
    
    try:
        cliente = MongoClient(MONGO_URI, serverSelectionTimeoutMS=MONGO_TIEMPO_FUERA)
        baseDatos = cliente[MONGO_BASEDATOS]
        coleccion=baseDatos[MONGO_COLECCION]
        ##4 CONSULTAS A LA VEZ
        datos_mongo = coleccion.aggregate(
                                        [
                                            {"$match": 
                                                {"$and":
                                                        [
                                                            {"pais":pais},
                                                            {"estacion":estacion},
                                                            {"Fecha_D":{"$gte": fec_unix_usuario}}
                                                        ]
                                                }
                                            },
                                            {
                                            "$project":{
                                                "_id":0,
                                                "Fecha_D_str":1,
                                                "Datos.Temperatura_D":1,
                                                "Datos.GDD_D":1,
                                                "Datos.Hr_D_%":1,
                                                "Datos.V_viento_D":1,
                                                "Datos.Energia_solar_D":1,
                                                "Datos.Precipitacion_D":1,
                                                "Datos.ET_D":1,

                                            }
                                            }
                                        ])
        datos_ = list(datos_mongo)
                
        return datos_
    except pymongo.errors.ServerSelectionTimeoutError as errorTiempo:
        return("Teimpo exedido"+ errorTiempo)
    except pymongo.errors.ConnectionFailure as errorConnexion:
        return("Fallo al conectarse a mongodb" + errorConnexion)
