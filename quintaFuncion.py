
import pymysql
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from datetime import date
#biblioteca Mongo
import pymongo
from pymongo import MongoClient
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

def BD_MONGO_RIEGO(pais, estacion, fec_unix_usuario):
    fec_inicial_unix = fec_unix_usuario-7*86400
    
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
                                                
                                                "Datos.ET_D":1,
                                                "Datos.Precipitacion_D":1,
                                            }
                                            }

                                        ])

        
        
        semana_gdd = list(datos)
        return semana_gdd
    except pymongo.errors.ServerSelectionTimeoutError as errorTiempo:
        return("Teimpo exedido"+ errorTiempo)
    except pymongo.errors.ConnectionFailure as errorConnexion:
        return("Fallo al conectarse a mongodb" + errorConnexion)


def RecomendacionHidrica(fec, estacion, dAparente, Hsuelo, tipo_riego):
    pais = 2  #colombia
    ##datos de entrada
    area_planta = 1
    Hvolumetrico = 70*dAparente
    HvolumOptimo = (Hvolumetrico/100)*0.25*area_planta*1000
    HvolumOptimo_hec = (Hvolumetrico/100)*0.25*10000*1000

    coefCultivo = 0.6
    HsueloVolumetrico = dAparente*Hsuelo ##ecuacion 6.6

    LaminaAguaDisponible_planta_m2 = (HsueloVolumetrico/100)*area_planta*0.25*1000
    LaminaAguaDisponible_planta_ha = (HsueloVolumetrico/100)*0.25*1000*10000

    
    
    #convertimos a string y unix y restamos el dia de consulta
    fec_string_usuario, fec_unix_usuario = convert_formato_fecha(fec)
    datos=BD_MONGO_RIEGO(pais, estacion, fec_unix_usuario)
    Vector_Grafica=[]
    RiegoL_D_suma = 0
    RiegoL_Ha_suma = 0
    for k in datos:
        fecha = k["Fecha_D_str"]
        et = k["Datos"]["ET_D"]
        precipitacion = k["Datos"]["Precipitacion_D"]
        evp_cultivo = et*coefCultivo
        evp_cultivo_2 = et*1.1

        RiegoL_D = (evp_cultivo-precipitacion)*area_planta*0.25
        RiegoL_Ha = (evp_cultivo-precipitacion)*10000*0.25
        RiegoL_D_suma += RiegoL_D
        RiegoL_Ha_suma += RiegoL_Ha

        Vector_Grafica.append((fecha, round(evp_cultivo_2,2), round(precipitacion,2)))

    RecomendacionLP = HvolumOptimo-(LaminaAguaDisponible_planta_m2+RiegoL_D_suma)
    RecomendacionLH = (HvolumOptimo_hec-(LaminaAguaDisponible_planta_ha+RiegoL_Ha_suma))/1000

    ef_riego = {'gravedad':(100/40),'aspersión':(100/70),'goteo': (100/90)}
    Rec_LP = RecomendacionLP*ef_riego[tipo_riego]
    Rec_L_Ha = RecomendacionLH*ef_riego[tipo_riego]
    return round(Rec_LP,2), round(Rec_L_Ha,2), Vector_Grafica

