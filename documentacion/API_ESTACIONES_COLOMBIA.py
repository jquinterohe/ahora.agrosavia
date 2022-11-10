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
import datetime
import numpy as np
#bibliotecas delta

from datetime import timedelta
#import datetime

#biblioteca Mongo
import pymongo
from pymongo import MongoClient
from bson.json_util import dumps, loads 


# MONGO_HOST = "127.0.0.1"
MONGO_HOST = "192.168.34.10"
MONGO_PUERTO ="27017"
MONGO_PWD = "ciba15153232"
MONGO_USER = "root"
MONGO_TIEMPO_FUERA =10000
MONGO_BASEDATOS = "PROYECTOC"
MONGO_COLECCION = "ESTACIONES"

MONGO_URI = "mongodb://"+ MONGO_USER +":"+ MONGO_PWD + "@"+MONGO_HOST +":" + MONGO_PUERTO + "/"

estacion_name =     {"1": "FUNDACIÓN"}
estacion_id =       {"1":"17053"}
estacion_lsid =       {"1": "57386"}
estacion_apy_key =  {"1": "xfcmxbygmi25nixeutcubwk0fcteh7vn"}
estacion_apy_secret = {"1": "upqnnlalw6bst8hgszrmvkhd0tniwcmq"}

def ESTACIONESTOTALES(estacionID, APIKEY, APISECRET, pais, estacion, lsid): #lsid:165611
    def Mensaje_Json(temp_actual,x,y):
        try:
            unix1=x
            unix2=y
            fecha1=print("fecha Inicio:",datetime.datetime.fromtimestamp(unix1)," :",x)
            fecha2=print("fecha Final:",datetime.datetime.fromtimestamp(unix2), " :",y)
            #fecha3=print("Hora actual", datetime.datetime.fromtimestamp(t1), " :",t1)
        
            parameters = {
            "station-id": "{}".format(estacionID), 
            "api-key": APIKEY,
            "t": temp_actual,
            "start-timestamp": x,
            "end-timestamp": y,
            "api-secret": APISECRET
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
                url = 'https://api.weatherlink.com/v2/historic/{}?api-key={}&t={}&start-timestamp={}&end-timestamp={}&api-signature={}'.format(parameters["station-id"], parameters["api-key"], parameters["t"],parameters["start-timestamp"],parameters["end-timestamp"], apiSignature)
                response = requests.get(url, params=None)
                if response.status_code == 200:
                    data_banano = json.loads(response.content)
                    return(data_banano)
        except:
            print("Error Funcion Mensaje Json")
    def test(data_banano):
        try:
            indice = data_banano['sensors']
            sensor1 =indice[0]
            datoss = sensor1['data']
            if datoss == []:
                return("Nothing")
            elif datoss != []:
                return("Data")
        except:
            print("error en la obtencion del json") 

    def fechas_Inicio_fin():
        temp_actual=int(time.time())
        x=  int(temp_actual-59*60) 
        y=  int(temp_actual + 0) 
        return temp_actual,x,y
    def ultimo_registro(data_banano):
        indice = data_banano['sensors']
        sensor1 =indice[0]
        unix_dato=int(sensor1['data'][0]['ts'])
        print("Unix de api:", unix_dato)
        try:
            cliente = MongoClient(MONGO_URI, serverSelectionTimeoutMS=MONGO_TIEMPO_FUERA)
            baseDatos = cliente[MONGO_BASEDATOS]
            coleccion=baseDatos[MONGO_COLECCION]
            cursor_UR = coleccion.find({"pais":pais, "estacion": estacion}).limit(1).sort([("$natural", -1)])
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
        {'pais':pais, 'estacion': estacion,'lsid': lsid, 'time': time, 'datos': [{'wind_speed_avg': None, 'wind_speed_hi': None, 'wind_chill': None, 'solar_rad_hi': None, 'deg_days_heat': None, 'bar': None, 'hum_out': None, 'temp_out': None, 'temp_out_lo': None, 'wet_bulb': None, 'temp_out_hi': None, 'solar_rad_avg': None, 'wind_run': None, 'solar_energy': None, 'dew_point_out': None, 'heat_index_out': None, 'thsw_index': None, 'rainfall_mm': None, 'deg_days_cool': None, 'rain_rate_hi_mm': None, 'et': None}]}
        ]
        contador=0
        for h in sensores:
            contador=contador+1
            id_sensor = h["lsid"]
            if id_sensor == Id:
                return(contador,h)

    def RellenarConDatosBlanco(Id,time):
        sensores=[
            {'pais':pais, 'estacion': estacion,"lsid": lsid, "data": [{'iss_reception': None, 'wind_speed_avg': None, 'wind_speed_hi': None, 'wind_dir_of_hi': None, 'wind_chill': None, 'solar_rad_hi': None, 'deg_days_heat': None, 'thw_index': None, 'bar': None, 'hum_out': None, 'temp_out': None, 'temp_out_lo': None, 'wet_bulb': None, 'temp_out_hi': None, 'solar_rad_avg': None, 'bar_alt': None, 'arch_int': None, 'wind_run': None, 'solar_energy': None, 'dew_point_out': None, 'rain_rate_hi_clicks': None, 'wind_dir_of_prevail': None, 'et': None, 'air_density': None, 'rainfall_in': None, 'heat_index_out': None, 'thsw_index': None, 'rainfall_mm': None, 'night_cloud_cover': None, 'deg_days_cool': None, 'rain_rate_hi_in': None, 'wind_num_samples': None, 'emc': None, 'rain_rate_hi_mm':None , 'rev_type': None, 'rainfall_clicks': None, 'ts': time, 'abs_press':None}]},
            ]
        contador=0
        for h in sensores:
            contador=contador+1
            id_sensor = h["lsid"]
            if id_sensor == Id:
                dat=h["data"]
                return(contador,dat[0])
    def extra_registros(k, lsid):
        if lsid==lsid: #sensor 2
            lista=["bar","temp_out","temp_out_hi","temp_out_lo", "hum_out",
                    "dew_point_out","wet_bulb", "wind_run","wind_speed_avg","wind_speed_hi",
                    "wind_chill","heat_index_out","rainfall_mm","rain_rate_hi_mm","deg_days_cool", 
                    "deg_days_heat", "thsw_index", "solar_rad_avg", "solar_energy", "solar_rad_hi", 
                    "et"]
            #La finalidad de este FOR solo es recorrer el diccionario clave-valor
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
            confirmaciones=len(confirmacion) ###para revisar por si hay claves que no se han registrado INT
            ## Creamos el JSON objetivo
            diccionario_registro={"pais": pais, "estacion": estacion,"lsid":lsid, "time":tiempo_unix, "datos":list_datos_registro}
            return diccionario_registro, "{}-{}".format(confirmaciones, lsid)
            

    def formato_json(data_banano, ts_last_BD):
        ### DE AQUI PARA ADELANTE SE UTILIZA EL JSON DE UNA SOLICITUD
        datos = data_banano["sensors"]
        count_G =1
        Id_sensor = []
        data = []
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
            sensores_interes= [lsid]       
            if lsid in sensores_interes:
                if not datos_por_sensor:
                    #CUANDO TODO EL DIA ESTÁ VACIO SE RELLENA CON DATOS NULOS
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
                else:                    
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
            #hasta aqui solo repasamos keys que son 4 , lsid, datos, ti_sensor, estructura
        return registros_totales, claves_encontradas, unix_iteracion   

    def insert_mongo_many(mydict):
        try:
            cliente = MongoClient(MONGO_URI, serverSelectionTimeoutMS=MONGO_TIEMPO_FUERA)
            baseDatos = cliente[MONGO_BASEDATOS]
            coleccion=baseDatos[MONGO_COLECCION]
            x = coleccion.insert_many(mydict)
            return "Datos insertado"

        except pymongo.errors.ServerSelectionTimeoutError as errorTiempo:
            return("Teimpo exedido"+ errorTiempo)
        except pymongo.errors.ConnectionFailure as errorConnexion:
            return("Fallo al conectarse a mongodb" + errorConnexion) 

    def Datos_menores_24(restante,unix_registro, temp_actual):
        x = unix_registro
        y = unix_registro + restante*60*60
        
        Json_dia = Mensaje_Json(temp_actual, x,y)
        ts_last_BD = x
        registros_totales, claves_encontradas, ts_last_BD_retornado =formato_json(Json_dia, ts_last_BD)
        paquetes=restante
        R_insert = insert_mongo_many(registros_totales)
        return(R_insert)

    def Datos_dias(dias,restante,unix_registro, temp_actual):
        y = unix_registro
        ts_last_BD=unix_registro #el ultimo dato registrado en la BD
        for i in range(dias):
            x = y
            y = x + 86400
            Json_dia = Mensaje_Json(temp_actual, x,y)
            paquetes=24
            registros_totales, claves_encontradas, ts_last_BD_retornado=formato_json(Json_dia,ts_last_BD)
            ts_last_BD=ts_last_BD_retornado
            R_insert = insert_mongo_many(registros_totales)
            print("Dia {} insertado".format(i+1))
        return(y)
        

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
            respuesta = insert_mongo_many(registros_totales)
            print(respuesta)
        elif result_UR == "New dateR":
            print("se tienen que recuperar datos")
            Datos_perdidos=datos_a_recuperar(unix_dato, unix_registro)
            print("Datos a recuperar:", Datos_perdidos)
            dias, restante= analisis_recuperacion(Datos_perdidos)
            print("dias:", dias, " ", "restante:", restante)

            if dias == 0:

                Datos_menores_24_R= Datos_menores_24(restante,unix_registro, temp_actual)
                print(Datos_menores_24_R)
                
            else:
                Datos_dias_R= Datos_dias(dias,restante,unix_registro, temp_actual)
                unix_registro=int(Datos_dias_R)
                Datos_menores_24_R= Datos_menores_24(restante,unix_registro, temp_actual)
                print(Datos_menores_24_R)
                print("Datos completamente recuperados")
            

        else: 
            print("El dato ya existe en la BD")

print("tamaño de estaciones:", len(estacion_id))
pais = 2
for i in range(len(estacion_id)):
    i=i+ 1
    estacion = i
    estacionID = estacion_id["{}".format(i)]
    APIKEY = estacion_apy_key["{}".format(i)]
    APISECRET = estacion_apy_secret["{}".format(i)]
    Name = estacion_name["{}".format(i)]
    lsid = estacion_lsid["{}".format(i)]

    """ print("valor de i:", i)
    print("estacio id:", estacionID, type(estacionID))
    print("APIKEY:", APIKEY, type(APIKEY))
    print("APISECRET:", APISECRET, type(APISECRET))
     """

    Resultados_estaciones =ESTACIONESTOTALES(estacionID,APIKEY,APISECRET, pais, estacion, lsid)
    print("Ejecutado estación {}". format(Name))
    print("____________________________________")
