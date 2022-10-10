def cambiar_formato_fecha(fecha):
    partes_fecha = fecha.split('-')

    return '{}{}{}{}{}'.format(partes_fecha[2],'/', partes_fecha[1],'/', partes_fecha[0])


def cambiar_formato_fecha_movil(fecha):
    partes_fecha = fecha.split('/')

    return '{}{}{}{}{}'.format(partes_fecha[1],'/', partes_fecha[0],'/20', partes_fecha[2])

###############################################################

from App import baseDatos, coleccion
def estaciones(Id_estacion):
    dict_estaciones = {"1":"Fundación","2":"otras"}
    estacionName=dict_estaciones[str(Id_estacion)]
    return estacionName

MONGO_COLECCION = "PRETRATAMIENTO"
coleccion=baseDatos[MONGO_COLECCION]
def estado_estaciones(pais):
    estaciones_disponibles = coleccion.aggregate(
                                    [                   
                                        {
                                            "$group":
                                                    {
                                                        "_id": "",
                                                        "estacion":{"$max":"$estacion"}
                                                    }
                                        }
                                    ]
                                )
    estaciones_disponibles=list(estaciones_disponibles)
    cantidad_Estaciones = estaciones_disponibles[0]["estacion"]
    print("cantidad de estaciones:", cantidad_Estaciones)
    #solicitamos los ultimos registros de cada estacion
    Registro_Estaciones = []
    
    for estacion in range(1,cantidad_Estaciones+1): #se suma uno porque Rangue cuenta desde Cero por lo tanto reduce una unidad
        datos = coleccion.aggregate(
                                    [
                                        {"$match": 
                                            {"$and":
                                                    [
                                                        {"pais":pais},
                                                        {"estacion":estacion},
                                                    ]
                                            }
                                        },
                                        {
                                        "$sort":{
                                            "_id":-1
                                                }
                                        },
                                        {
                                        "$limit":1
                                        },
                                    ])
        datos = list(datos)
        estacion_ = datos[0]["estacion"]
        Nombre_ = estaciones(estacion_)
        fecha_ = datos[0]["Fecha_D_str"]

        Registro_Estaciones.append((estacion_,Nombre_, fecha_))
        
    print("registro de staciones", Registro_Estaciones)
    return cantidad_Estaciones, Registro_Estaciones

def Visita(mail):
    from datetime import datetime
    visitas = {"Visita": 1,"usuario": mail ,"Tipo":"Aplicativo web" ,"Fecha_utc": datetime.utcnow(), "Fecha_local": datetime.now()}
    return visitas

def Visita_movil(mail):
    from datetime import datetime
    visitas = {"Visita": 1,"usuario": mail ,"Tipo":"Móvil" ,"Fecha_utc": datetime.utcnow(), "Fecha_local": datetime.now()}
    return visitas

def generate_random_string():
    import random
    import string
    length=8
    letters = string.ascii_lowercase
    rand_string = ''.join(random.choice(letters) for i in range(length))
    return rand_string

from segundaFuncion import BD_MONGO_DATOS
from segundaFuncion import convert_formato_fecha_forward


###para consultar a la base de datos
def historicos(fec, estacion):
    pais = 2 #2 colombia
    #convertimos a string y unix y restamos el dia de consulta
    fec_string_usuario, fec_unix_usuario = convert_formato_fecha_forward(fec)
    ##solicitamos datos
    datos = BD_MONGO_DATOS(pais, estacion, fec_unix_usuario)
    Vector_datos=[]
    GDA_acum = 0
    TEMP_acum = 0
    HUM_acum = 0
    GDA = 0
    gdd = 0
    for k in datos:
        gdd = k["Datos"]["GDD_D"]
        fecha = k["Fecha_D_str"]
        humedad = k["Datos"]["Hr_D_%"]
        temperatura = k["Datos"]["Temperatura_D"]
        viento = k["Datos"]["V_viento_D"]
        Energia_solar = k["Datos"]["Energia_solar_D"]
        Precipitacion = k["Datos"]["Precipitacion_D"]
        ET = k["Datos"]["ET_D"]
        
        Vector_datos.append((fecha, round(temperatura,2), round(humedad,2),
                            round(viento,2), round(Energia_solar/0.0864,2),round(Precipitacion,2), round(ET,2)))
        if GDA_acum >= 900:
            break 
    
    return Vector_datos
