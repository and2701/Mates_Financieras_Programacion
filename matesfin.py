"""
V1
Autor: Andrea Acosta Actuaria 
Fecha: 7 de Octubre del 2026
Solicitud: Consulta Banxico tiempo real seriesX, calcular IS
Datos de entrada:
Datos de salida: Consulta seriesX y calcular interes simple
"""
import os
import time
import requests
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv

load_dotenv()

SERIE_BANXICO = "SF60648"
TOKEN = os.getenv("BANXICO_TOKEN")
CORREO = os.getenv("CORREO_ORIGEN")
CLAVE_CORREO = os.getenv("CORREO_PASSWORD")
SERVIDOR = os.getenv("SMTP_SERVER", "smtp.gmail.com")
PUERTO = int(os.getenv("SMTP_PORT", "465"))

ejecutar = True


def obtener_serie_banxico():
    """
    Consulta la serie seleccionada en Banxico mediante su API, muestra la fecha y el valor mas reciente, y devuelve la tasa como numero.
    """
    if not TOKEN:
        print("Configura el token de Banxico en el archivo .env")
        return None

    direccion = f"https://www.banxico.org.mx/SieAPIRest/service/v1/series/{SERIE_BANXICO}/datos"
    cabeceras = {"Bmx-Token": TOKEN, "Accept": "application/json"}

    try:
        resultado = requests.get(direccion, headers=cabeceras, timeout=15)
        print("Estado de conexion:", resultado.status_code)
        resultado.raise_for_status()

        serie_datos = resultado.json()["bmx"]["series"][0]["datos"]

        if len(serie_datos) == 0:
            print("No hay datos disponibles para esta serie.")
            return None

        ultimo = serie_datos[-1]
        valor = float(ultimo["dato"].replace(",", ""))

        print("\nConsulta realizada correctamente")
        print("Clave de serie:", SERIE_BANXICO)
        print("Fecha del registro:", ultimo["fecha"])
        print("Tasa registrada:", ultimo["dato"])

        return valor

    except requests.exceptions.RequestException as error:
        print("No fue posible conectar con Banxico:", error)
    except (KeyError, IndexError, ValueError, TypeError) as error:
        print("No se pudieron interpretar los datos:", error)

    return None


def crear_reporte(tasa, capital, dias):
    """
    Genera un reporte de interes simple con la tasa consultada, el capital inicial y el plazo en dias. Calcula el interes y el monto 
    total, y devuelve la informacion en texto.
    """
    interes = capital * (tasa / 100) * (dias / 360)
    total = capital + interes

    texto = (
        "REPORTE FINANCIERO: INTERES SIMPLE\n"
        "==================================\n"
        f"Serie Banxico consultada: {SERIE_BANXICO}\n"
        f"Tasa anual: {tasa:.4f}%\n"
        f"Capital inicial: ${capital:,.2f}\n"
        f"Plazo: {dias} dias\n"
        f"Interes simple generado: ${interes:,.2f}\n"
        f"Monto total acumulado: ${total:,.2f}\n"
    )

    return texto


def guardar_y_enviar(texto):
    """
    Guarda el reporte financiero en un archivo de texto y solicita un correo de destino para enviarlo.
    Si ocurre un error, informa al usuario y conserva el archivo.
    """
    archivo_txt = "resultado_interes.txt"

    with open(archivo_txt, "w", encoding="utf-8") as documento:
        documento.write(texto)

    print("Se guardo el reporte en", archivo_txt)

    if not CORREO or not CLAVE_CORREO:
        print("Falta configurar el correo de origen en .env.")
        print("El archivo esta guardado, pero no se envio.")
        return

    destino = input("Escribe el correo del destinatario: ").strip()

    if not destino:
        print("No se ingreso un destinatario.")
        return

    correo_mensaje = EmailMessage()
    correo_mensaje["Subject"] = "Resultados del interes simple"
    correo_mensaje["From"] = CORREO
    correo_mensaje["To"] = destino
    correo_mensaje.set_content(texto)

    try:
        with smtplib.SMTP_SSL(SERVIDOR, PUERTO, timeout=30) as conexion:
            conexion.login(CORREO.strip(), CLAVE_CORREO.strip().replace(" ", ""))
            conexion.send_message(correo_mensaje)

        print("Envio completado correctamente.")
        print("Correo receptor:", destino)

    except smtplib.SMTPAuthenticationError:
        print("No se pudo autenticar la cuenta.")
        print("Revisa tu correo y la contrasena de aplicacion.")
    except (smtplib.SMTPException, OSError) as error:
        print("Error durante el envio:", error)
        print("Puedes consultar el reporte guardado.")
    except Exception as error:
        print("Se presento un error inesperado:", error)
        print("El reporte permanece guardado.")


def calcular_interes():
    """
    Obten la tasa actual de Banxico, solicita el capital inicial y el plazo, valida los datos y calcula el interes simple.
    Muestra el reporte, espera cinco segundos, llama a la funcion y envia los resultados.
    """
    tasa_actual = obtener_serie_banxico()

    if tasa_actual is None:
        print("No se realizara el calculo sin una tasa valida.")
        return

    try:
        capital = float(input("Ingresa el capital inicial: $"))
        plazo = int(input("Ingresa el plazo en dias (7 a 28): "))

        if capital <= 0:
            print("El capital debe ser positivo.")
            return

        if not 7 <= plazo <= 28:
            print("El plazo permitido es de 7 a 28 dias.")
            return

        resultado = crear_reporte(tasa_actual, capital, plazo)
        print("\n" + resultado)

        print("El reporte se enviara en 5 segundos...")
        time.sleep(5)
        guardar_y_enviar(resultado)

    except ValueError:
        print("Ingresa un capital y un plazo con formato numerico valido.")


def mostrar_menu():
    """
    Muestra las opciones disponibles del programa y solicita al usuario que seleccione una.
    """
    print("\n--- CONSULTA FINANCIERA BANXICO ---")
    print("1. Consultar Banxico series X")
    print("2. Calcular interes simple")
    print("3. Terminar programa")
    return input("Elige una opcion: ").strip()


while ejecutar:
    opcion = mostrar_menu()

    if opcion == "1":
        obtener_serie_banxico()

    elif opcion == "2":
        calcular_interes()

    elif opcion == "3":
        print("Programa finalizado. Gracias.")
        ejecutar = False

    else:
        print("Opcion incorrecta. Selecciona 1, 2 o 3.")