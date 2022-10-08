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


def BD_MONGO_NUTRIENTES_VCOLOMBIA(semanas, pais, estacion, fec_unix_usuario):
    fec_inicial_unix = fec_unix_usuario-semanas*86400*7
    
    try:
        cliente = MongoClient(MONGO_URI, serverSelectionTimeoutMS=MONGO_TIEMPO_FUERA)
        baseDatos = cliente[MONGO_BASEDATOS]
        coleccion=baseDatos[MONGO_COLECCION]
        ##4 CONSULTAS A LA VEZ
        datos = coleccion.aggregate(
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
                                            "$project":{
                                                "_id":0,
                                                "Fecha_D_str":1,
                                                
                                                "Datos.GDD_D":1,
                                                "Datos.Energia_solar_D":1,
                                            }
                                            }

                                        ])

        
        
        semana_gdd = list(datos)
        return semana_gdd
    except pymongo.errors.ServerSelectionTimeoutError as errorTiempo:
        return("Teimpo exedido"+ errorTiempo)
    except pymongo.errors.ConnectionFailure as errorConnexion:
        return("Fallo al conectarse a mongodb" + errorConnexion)


def nutrientes(fec, estacion, rPA, semanas):
    pais = 2# 2 colombia
    print("Fecha ingresada por el usuario:", fec)
    #convertimos a string y unix y restamos el dia de consulta
    fec_string_usuario, fec_unix_usuario = convert_formato_fecha(fec)
    print("Fecha a ingresar a calculo:", fec_string_usuario)
    ##solicitamos datos
    datos=BD_MONGO_NUTRIENTES_VCOLOMBIA(semanas, pais, estacion, fec_unix_usuario)
    
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
        Vector_datos.append((fecha,round(GDA_acum,2), round(ES_ACUMULADO,2)))
    
    print("ES_ACUMULADO:",ES_ACUMULADO)
    matSeca = 1.5*ES_ACUMULADO*(1-np.exp(-0.7*3.5)) #g
    #0.25 es biomasa seca de de toda la planta y divimos entre 1000 para convertir el resultado a kg
    biomasa_planta = matSeca*((10000/rPA)/1000)/0.25 #resultado en kg

    biomasa_planta=round(biomasa_planta,1)

    biomasa = biomasa_planta*rPA

    masaN = round((((biomasa_planta*2)/1000)*1000),2)
    masaP= round((((biomasa_planta*0.4)/1000)*1000),2)
    masaK = round((((biomasa_planta*6)/1000)*1000),2)
    masaCa = round((((biomasa_planta*1)/1000)*1000),2)
    masaMg = round((((biomasa_planta*0.18)/1000)*1000),2)
    masaS = round((((biomasa_planta*0.1)/1000)*1000),2)
    masaFe= round((((biomasa_planta*1000)*3.88)/(1000*1000)),2)
    masaCu = round((((biomasa_planta*1000)*0.77)/(1000*1000)),2)
    masaMn = round((((biomasa_planta*1000)*1.23)/(1000*1000)),2)
    masaSn = round((((biomasa_planta*1000)*1.12)/(1000*1000)),2)
    masaB = round((((biomasa_planta*1000)*1.37)/(1000*1000)),2)

    """ print("masaN:",masaN)
    print("masaP:",masaP) 
    print("masaK:",masaK) 
    print("masaCa:",masaCa) 
    print("masaMg:",masaMg) 
    print("masaS:",masaS) 
    print("masaFe:",masaFe) 
    print("masaCu:",masaCu) 
    print("masaMn:",masaMn) 
    print("masaSn:",masaSn) 
    print("masaB:",masaB) """ 

    masaN_hectarea = round((masaN*rPA/1000),2)
    masaP_hectarea= round((masaP*rPA/1000),2)
    masaK_hectarea = round((masaK*rPA/1000),2)
    masaCa_hectarea = round((masaCa*rPA/1000),2)
    masaMg_hectarea = round((masaMg*rPA/1000),2)
    masaS_hectarea = round((masaS*rPA/1000),2)
    masaFe_hectarea= round((masaFe*rPA/1000),2)
    masaCu_hectarea = round((masaCu*rPA/1000),2)
    masaMn_hectarea = round((masaMn*rPA/1000),2)
    masaSn_hectarea = round((masaSn*rPA/1000),2)
    masaB_hectarea = round((masaB*rPA/1000),2)

    """ print("masaN_hectarea:",masaN_hectarea)
    print("masaP_hectarea:",masaP_hectarea) 
    print("masaK_hectarea:",masaK_hectarea) 
    print("masaCa_hectarea:",masaCa_hectarea) 
    print("masaMg_hectarea:",masaMg_hectarea) 
    print("masaS_hectarea:",masaS_hectarea) 
    print("masaFe_hectarea:",masaFe_hectarea) 
    print("masaCu_hectarea:",masaCu_hectarea) 
    print("masaMn_hectarea:",masaMn_hectarea) 
    print("masaSn_hectarea:",masaSn_hectarea) 
    print("masaB_hectarea:",masaB_hectarea) """

    tupla1 = ("N","P", "K", "Ca", "Mg", "S", "Fe", "Cu", "Mn", "Sn", "B")
    tupla2= (masaN,masaP, masaK,masaCa, masaMg,masaS,masaFe,masaCu,masaMn,masaSn,masaB)
    tupla3=(masaN_hectarea,masaP_hectarea,masaK_hectarea,masaCa_hectarea,masaMg_hectarea,masaS_hectarea,masaFe_hectarea,masaCu_hectarea,masaMn_hectarea,masaSn_hectarea,masaB_hectarea)
    tupla=[]
    for k in range(0,11):
        #print("valor de k:",k)
        tupla.append((tupla1[k], tupla2[k], tupla3[k]))
    #print("tupla:", tupla)
    print("Funcion 4 ejecutado correctamente")
    return(fec, biomasa_planta, biomasa, tupla)

