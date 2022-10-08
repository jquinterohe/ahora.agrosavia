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
##CREDENCIALES DE LA BASE DE DATOS
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

     
def BD_MONGOF1(pais, estacion, fec_unix_usuario):
    fec14_unix = fec_unix_usuario-14*86400
    fec28_unix = fec_unix_usuario-28*86400
    
    try:
        cliente = MongoClient(MONGO_URI, serverSelectionTimeoutMS=MONGO_TIEMPO_FUERA)
        baseDatos = cliente[MONGO_BASEDATOS]
        coleccion=baseDatos[MONGO_COLECCION]
        ##4 CONSULTAS A LA VEZ
        GDD14 = coleccion.aggregate(
                                        [
                                            {"$match": 
                                                {"$and":
                                                        [
                                                            {"pais":pais},
                                                            {"estacion":estacion},
                                                            {"Fecha_D":{"$gt": fec14_unix ,"$lte":fec_unix_usuario}}
                                                        ]
                                                }
                                            },
                                            
                                            {
                                                "$group":
                                                        {
                                                            "_id": "$estacion",
                                                            "Registros_dia":{"$sum":1},
                                                            
                                                            "GDA_14" : {"$sum" : "$Datos.GDD_D"},
                                                        }
                                            },
                                            {
                                                "$addFields":
                                                            {
                                                                "nHojas14" : {"$round":[{"$divide" : ["$GDA_14", 108]},1]}
                                                                
                                                            }
                                            }

                                        ])
        GDD_TEST_14 = coleccion.aggregate(
                                        [
                                            {"$match": 
                                                {"$and":
                                                        [
                                                            {"pais":pais},
                                                            {"estacion":estacion},
                                                            {"Fecha_D":{"$gt": fec14_unix ,"$lte":fec_unix_usuario}}
                                                        ]
                                                }
                                            }

                                        ])
        GDD28 = coleccion.aggregate(
                                        [
                                            {"$match": 
                                                {"$and":
                                                        [
                                                            {"pais":pais},
                                                            {"estacion":estacion},
                                                            {"Fecha_D":{"$gt": fec28_unix ,"$lte":fec_unix_usuario}}
                                                        ]
                                                }
                                            },
                                            {
                                                "$group":
                                                        {
                                                            "_id": "$estacion",
                                                            "Dias_contados":{"$sum":1},
                                                            
                                                            "GDA_28" : {"$sum" : "$Datos.GDD_D"}
                                                        }
                                            },
                                            {
                                                "$addFields":
                                                            {
                                                                "nHojas28" : {"$round":[{"$divide" : ["$GDA_28", 108]},1]}
                                                                
                                                            }
                                            }

                                        ])
        GDD_TEST_28 = coleccion.aggregate(
                                        [
                                            {"$match": 
                                                {"$and":
                                                        [
                                                            {"pais":pais},
                                                            {"estacion":estacion},
                                                            {"Fecha_D":{"$gt": fec28_unix ,"$lte":fec_unix_usuario}}
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
        
        gdd14 = list(GDD14)
        gdd_test_14 = list(GDD_TEST_14)
        gdd28 = list(GDD28)
        gdd_test_28 = list(GDD_TEST_28)
        
        return gdd14, gdd_test_14, gdd28, gdd_test_28
    except pymongo.errors.ServerSelectionTimeoutError as errorTiempo:
        return("Teimpo exedido"+ errorTiempo)
    except pymongo.errors.ConnectionFailure as errorConnexion:
        return("Fallo al conectarse a mongodb" + errorConnexion)

#enviamos a cambiar formato a la fecha
def NumeroHojas(fec, estacion):
    pais = 2#1 peru
    print("Fecha ingresada por el usuario:", fec)
    #convertimos a string y unix y restamos el dia de consulta
    fec_string_usuario, fec_unix_usuario = convert_formato_fecha(fec)
    print("Fecha a ingresar a calculo:", fec_string_usuario)
    ##solicitamos datos
    gdd14, gdd_test_14, gdd28, gdd_test_28 =BD_MONGOF1(pais, estacion, fec_unix_usuario)
    NHojas14 = gdd14[0]["nHojas14"]
    NHojas28 = gdd28[0]["nHojas28"]

    Vector_Grafica = []
    for k in gdd_test_28:
        fecha = k["Fecha_D_str"]
        temperatura = k["Datos"]["Temperatura_D"]
        gdd = k["Datos"]["GDD_D"]
        Vector_Grafica.append((fecha, round(temperatura,2), round(gdd,2)))
        #print("Fecha:", fecha, " ","Temperatura:", temperatura , " ", "GDD:", gdd)
    return NHojas14, NHojas28, Vector_Grafica


#                       OPCION DE CALCULO POR SEMANA
     
def BD_MONGOF2(pais, estacion, fec_unix_usuario, nrosemanas):
    fec_inicial_unix = fec_unix_usuario-7*86400*nrosemanas
    
    try:
        cliente = MongoClient(MONGO_URI, serverSelectionTimeoutMS=MONGO_TIEMPO_FUERA)
        baseDatos = cliente[MONGO_BASEDATOS]
        coleccion=baseDatos[MONGO_COLECCION]
        ##4 CONSULTAS A LA VEZ
        gdd_semanas = coleccion.aggregate(
                                        [
                                            {"$match": 
                                                {"$and":
                                                        [
                                                            {"pais":pais},
                                                            {"estacion":estacion},
                                                            {"Fecha_D":{"$gt": fec_inicial_unix ,"$lte":fec_unix_usuario}}
                                                        ]
                                                }
                                            },
                                            
                                            {
                                                "$group":
                                                        {
                                                            "_id": "$estacion",
                                                            "Registros_dia":{"$sum":1},
                                                            
                                                            "GDA" : {"$sum" : "$Datos.GDD_D"},
                                                        }
                                            },
                                            {
                                                "$addFields":
                                                            {
                                                                "nHojas" : {"$round":[{"$divide" : ["$GDA", 108]},1]}
                                                                
                                                            }
                                            }

                                        ])
        semanas_test = coleccion.aggregate(
                                        [
                                            {"$match": 
                                                {"$and":
                                                        [
                                                            {"pais":pais},
                                                            {"estacion":estacion},
                                                            {"Fecha_D":{"$gt": fec_inicial_unix ,"$lte": fec_unix_usuario}}
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
        
        
        semana_gdd = list(gdd_semanas)
        semana_test = list(semanas_test)
        
        return semana_gdd, semana_test
    except pymongo.errors.ServerSelectionTimeoutError as errorTiempo:
        return("Teimpo exedido"+ errorTiempo)
    except pymongo.errors.ConnectionFailure as errorConnexion:
        return("Fallo al conectarse a mongodb" + errorConnexion)

def NumeroHojasSemanas(fec, estacion, nrosemanas):
    pais = 2#1 peru
    print("Fecha ingresada por el usuario:", fec)
    #convertimos a string y unix y restamos el dia de consulta
    fec_string_usuario, fec_unix_usuario = convert_formato_fecha(fec)
    print("Fecha a ingresar a calculo:", fec_string_usuario)
    ##solicitamos datos
    semana_gdd, semana_test=BD_MONGOF2(pais, estacion, fec_unix_usuario, nrosemanas)

    NHojas = semana_gdd[0]["nHojas"]

    Vector_Grafica = []
    for k in semana_test:
        fecha = k["Fecha_D_str"]
        temperatura = k["Datos"]["Temperatura_D"]
        gdd = k["Datos"]["GDD_D"]
        Vector_Grafica.append((fecha, round(temperatura,2), round(gdd,2)))
        #print("Fecha:", fecha, " ","Temperatura:", temperatura , " ", "GDD:", gdd)
    return NHojas, Vector_Grafica
