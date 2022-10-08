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


### opcion 1 backward
def convert_formato_fecha(fec):
    fec = datetime.strptime(fec, '%d/%m/%Y')
    #restamos 1 dia que es el de consulta
    fec_string = fec
    fec =fec -timedelta(1)
    fec_unix=int(time.mktime(fec.timetuple()))
    if fec.month < 10:
        fec = str(fec.day)+'/0'+str(fec.month)+'/'+str(fec.year)
    else:
        fec = str(fec.day)+'/'+str(fec.month)+'/'+str(fec.year)

    ##
    if fec_string.month < 10:
        fec_string = str(fec_string.day)+'/0'+str(fec_string.month)+'/'+str(fec_string.year)
    else:
        fec_string = str(fec_string.day)+'/'+str(fec_string.month)+'/'+str(fec_string.year)
        
    return(fec, fec_unix, fec_string)


def BD_MONGO_BIOMASA_F1(pais, estacion, fec_unix_usuario): ###regresa valores menores e iguales que fecha de consulta
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
                                                "Datos.GDD_D":1,
                                                "Datos.Hr_D_%":1,
                                                "Datos.Energia_solar_D":1
                                            }
                                            }
                                        ])
        datos_ = list(datos_mongo)
                
        return datos_
    except pymongo.errors.ServerSelectionTimeoutError as errorTiempo:
        return("Teimpo exedido"+ errorTiempo)
    except pymongo.errors.ConnectionFailure as errorConnexion:
        return("Fallo al conectarse a mongodb" + errorConnexion)


def EstimacionRacimoCicloAnterior(fec, estacion, rPA, Cant_manos):
    pais = 2#1 peru
    print("Fecha ingresada por el usuario:", fec)
    #convertimos a string y unix y restamos el dia de consulta
    fec_string_usuario, fec_unix_usuario, fec_string = convert_formato_fecha(fec)
    print("Fecha a ingresar a calculo:", fec_string_usuario)
    ##solicitamos datos
    datos = BD_MONGO_BIOMASA_F1(pais, estacion, fec_unix_usuario)

    ##invertir lista
    datos_new = list(reversed(datos))
    Vector_datos=[]
    GDA_acum = 0
    ES_ACUMULADO=0
    vector_temp = []
    vector_gda = []
    vector_fecha = []
    vector_gda_acum=[]    
    for k in datos_new:
        gdd = k["Datos"]["GDD_D"]
        GDA_acum += gdd
        fecha = k["Fecha_D_str"]
        energia_solar = k["Datos"]["Energia_solar_D"]
        ES_ACUMULADO += energia_solar
        vector_gda.append(gdd)
        vector_gda_acum.append(GDA_acum)
        vector_fecha.append(fecha)
        Vector_datos.append((fecha, round(gdd,2) ,round(GDA_acum,2), round(ES_ACUMULADO,2)))
        if GDA_acum >= 900:
            break
    semanas=math.ceil((len(Vector_datos))/7)
    #matSeca = 1.5*RadAcc*(1-np.exp(-0.7*3.5))
    matSeca = 1.5*ES_ACUMULADO*(1-np.exp(-0.7*3.5))
    biomasa_planta = matSeca*(10000/rPA)/1000/0.25
    #print("biomasa total:", biomasa_planta)
    biomasa_planta=round((biomasa_planta*(Cant_manos/12)),1)
    biomasa = round((biomasa_planta*rPA)/1000,2)#lo pasamos a hectareasbiomasa = biomasa_planta*rPA
    return fec_string, biomasa_planta, biomasa, semanas

###opcion 2 FORWARD

def convert_formato_fecha_forward(fec):
    fec = datetime.strptime(fec, '%d/%m/%Y')
    fec_date = fec
    #restamos 1 dia que es el de consulta
    fec_unix=int(time.mktime(fec.timetuple()))
    if fec.month < 10:
        fec = str(fec.day)+'/0'+str(fec.month)+'/'+str(fec.year)
    else:
        fec = str(fec.day)+'/'+str(fec.month)+'/'+str(fec.year)
        
    return(fec, fec_unix, fec_date)

def BD_MONGO_BIOMASA_F2(pais, estacion, fec_unix_usuario): ###regresa valores menores e iguales que fecha de consulta -1
    
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
                                                "Datos.Energia_solar_D":1
                                            }
                                            }
                                        ])
        datos_ = list(datos_mongo)
                
        return datos_
    except pymongo.errors.ServerSelectionTimeoutError as errorTiempo:
        return("Teimpo exedido"+ errorTiempo)
    except pymongo.errors.ConnectionFailure as errorConnexion:
        return("Fallo al conectarse a mongodb" + errorConnexion)

def EstimacionRacimoProyeccion(fec, estacion,rPA, Cant_manos):
    pais = 2#1 peru
    print("Fecha ingresada por el usuario:", fec)
    #convertimos a string y unix y restamos el dia de consulta
    fec_string_usuario, fec_unix_usuario,fec_date = convert_formato_fecha_forward(fec)
    print("Fecha a ingresar a calculo:", fec_string_usuario)
    ##solicitamos datos
    datos = BD_MONGO_BIOMASA_F2(pais, estacion, fec_unix_usuario)
    Vector_datos=[]
    GDA_acum = 0
    gdd = 0
    ES_ACUMULADO=0
    for k in datos:
        gdd = k["Datos"]["GDD_D"]
        GDA_acum += gdd
        fecha = k["Fecha_D_str"]
        energia_solar = k["Datos"]["Energia_solar_D"]
        ES_ACUMULADO += energia_solar

        Vector_datos.append((fecha, round(GDA_acum,2), round(ES_ACUMULADO,2)))
        if GDA_acum >= 900:
            break#print("valor de k1:", k, "sumatoria:", GDA_acum)
    #print("GDA ACUMULADO PARA DESICIÓN::", GDA_acum) 
    #
    if GDA_acum <900:
        GDA_DATOS_REALES=GDA_acum
        datos_tomados=int(len(Vector_datos)) #dias tomados en cuenta
        gda_promedio = GDA_acum/datos_tomados
        esolar_promedio = ES_ACUMULADO/datos_tomados
        gda_Restantes = 900-GDA_acum
        estimacion = math.ceil(gda_Restantes/gda_promedio)
        #estimacion de energia solar para el futuro
        estimacionESolar = estimacion*esolar_promedio
        esolarTotal = ES_ACUMULADO + estimacionESolar
        dias_totales = datos_tomados + estimacion
        fec_final = fec_date + timedelta(dias_totales)
        fec_final = fec_final.strftime("%d/%m/%Y")
        nSemanas=round((estimacion)/7, 2)
        #1.5g es lo que se genera por cada 1MJ/m2 absorvido
        matSeca = 1.5*esolarTotal*(1-np.exp(-0.7*3.5)) #g
        #0.25 es biomasa seca de de toda la planta y divimos entre 1000 para convertir el resultado a kg
        biomasa_planta = matSeca*((10000/rPA)/1000)/0.25 #resultado en kg
        biomasa_planta=round((biomasa_planta*(Cant_manos/12)),1)
        biomasa = round(biomasa_planta*rPA,1)/1000
        return  fec_string_usuario,fec_final,biomasa_planta ,biomasa ,estimacion, nSemanas
    
    else:
        datos_tomados=int(len(Vector_datos)) #dias tomados en cuenta
        #print("cantidad de datos:", datos_tomados)
        nSemanas=round((len(Vector_datos))/7, 1)
        estimacion=0
        fec_final = fecha
        matSeca = 1.5*ES_ACUMULADO*(1-np.exp(-0.7*3.5)) #g
        #0.25 es biomasa seca de de toda la planta y divimos entre 1000 para convertir el resultado a kg
        biomasa_planta = matSeca*((10000/rPA)/1000)/0.25 #resultado en kg
        biomasa_planta=round((biomasa_planta*(Cant_manos/12)),1)
        biomasa = round(biomasa_planta*rPA,1)/1000

        return  fec_string_usuario,fec_final,biomasa_planta ,biomasa ,estimacion, nSemanas
    
