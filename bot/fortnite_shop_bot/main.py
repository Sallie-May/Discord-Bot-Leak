import discord
import requests
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv
import os
from datetime import datetime
from pytz import timezone, UTC

# Cargar variables de entorno
load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
API_KEY = os.getenv('FORTNITE_API_KEY')
CHANNEL_ID = 1328823915190947993  # ID del canal donde quieres enviar los mensajes
API_URL = "https://fortnite-api.com/v2/shop"  # URL de la API

# Configurar el cliente de Discord
intents = discord.Intents.default()
client = discord.Client(intents=intents)
scheduler = AsyncIOScheduler()

async def enviar_tienda():
    """Obtiene y envía la tienda de Fortnite."""
    headers = {'Authorization': API_KEY}
    try:
        response = requests.get(API_URL, headers=headers)
        data = response.json()

        if response.status_code == 200:
            # Obtener la fecha de actualización y convertirla a hora de Ecuador
            fecha_actualizacion_utc = data["data"]["date"]
            utc = UTC
            ecuador = timezone("America/Guayaquil")
            fecha_utc = utc.localize(datetime.strptime(fecha_actualizacion_utc, "%Y-%m-%dT%H:%M:%SZ"))
            fecha_ecuador = fecha_utc.astimezone(ecuador)
            fecha_legible = fecha_ecuador.strftime("%d %B %Y")

            # Enviar mensaje inicial
            channel = client.get_channel(CHANNEL_ID)
            await channel.send(
                "🌟🌟🌟 **__TIENDA DE FORTNITE__** 🌟🌟🌟\n"
                f"🗓️ **Fecha de actualización:** `{fecha_legible}`\n"
                "✨ ¡Descubre las novedades del día! ✨"
            )

            # Procesar los artículos
            tienda_items = data["data"]["entries"]
            grupos = {}

            for item in tienda_items:
                # Excluir artículos musicales y de carros
                if "tracks" in item and item["tracks"]:
                    continue
                if "bundle" in item or item.get("layout", {}).get("category", "").lower() == "start your engines":
                    continue

                # Verificar que el artículo tenga imagen
                if "newDisplayAsset" in item and item["newDisplayAsset"]["materialInstances"]:
                    imagen = item["newDisplayAsset"]["materialInstances"][0]["images"].get("OfferImage", None)
                else:
                    continue

                # Organizar artículos por grupo
                grupo = item.get("layout", {}).get("name", "Otros")
                if grupo not in grupos:
                    grupos[grupo] = []

                nombre = item["devName"].replace("[VIRTUAL]", "").strip()
                if "," in nombre:
                    nombre = nombre.split(",")[0].strip()

                precio = item["finalPrice"]
                if precio <= 0:
                    precio = "Paquete especial"

                grupos[grupo].append({"nombre": nombre, "precio": precio, "imagen": imagen})

            # Enviar los grupos al canal
            for grupo, skins in grupos.items():
                for skin in skins:
                    embed = discord.Embed(
                        title=f"🛒 {grupo} - {skin['nombre']}",
                        description=f"Precio: {skin['precio']} V-Bucks",
                        color=0x1a1a1a
                    )
                    if skin["imagen"]:
                        embed.set_image(url=skin["imagen"])
                    await channel.send(embed=embed)
        else:
            print(f"Error al obtener la tienda: {data.get('error', 'Desconocido')}")
    except Exception as e:
        print(f"Error al enviar la tienda: {e}")


@client.event
async def on_ready():
    print(f"Bot conectado como {client.user}")
    # Programa la tarea diaria a las 12:00 AM UTC
    scheduler.add_job(enviar_tienda, 'cron', hour=0, minute=0, timezone='UTC')
    scheduler.start()


# Iniciar el bot
client.run(DISCORD_TOKEN)
