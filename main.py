import re
import asyncio
import httpx
import csv
import os
from datetime import datetime


async def fetchGeocode(city):
    try:
        url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}"
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url)
            data = resp.json()
            if data.get("results"):
                res = data["results"][0]
                return {
                    "error": False,
                    "latitude": res["latitude"],
                    "longitude": res["longitude"],
                }
            return {
                "error": True,
            }

    except httpx.ConnectTimeout:
        print("Timeout error: the request took too long.")
        return {"error": True}

    except httpx.ReadTimeout:
        print("Reading response took too long!")

    except httpx.ConnectError:
        print("Connection error: could not reach the server.")
        return {"error": True}

    except httpx.RequestError as e:
        print(f"Request error: {e}")
        return {"error": True}


async def fetchWeather(lat, lon):
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url)
            data = resp.json()["current_weather"]
            return [data["temperature"], data["windspeed"]]

    except httpx.ConnectTimeout:
        print("Timeout error: the request took too long.")
        return {"error": True}

    except httpx.ReadTimeout:
        print("Reading response took too long!")

    except httpx.ConnectError:
        print("Connection error: could not reach the server.")
        return {"error": True}

    except httpx.RequestError as e:
        print(f"Request error: {e}")
        return {"error": True}


async def processCity(city):
    geo = await fetchGeocode(city)

    if not geo["error"]:
        weather = await fetchWeather(geo["latitude"], geo["longitude"])
        weather.insert(0, city)
        return weather
    return {"error": True, "city": city}


def parseCityInput(input_str):
    cities = re.split(r"\s*[,:\s]\s*", input_str.strip())
    return [city for city in cities if city]


def printWeatherTable(data):
    headers = ["City", "Temp [°C]", "Wind [km/h]"]

    col_widths = [
        max(len(str(row[0])) for row in data + [headers]),
        max(len(str(row[1])) for row in data + [headers]),
        max(len(str(row[2])) for row in data + [headers]),
    ]

    header_line = " | ".join(str(h).ljust(w) for h, w in zip(headers, col_widths))
    print(header_line)

    for row in data:
        line = " | ".join(str(cell).ljust(w) for cell, w in zip(row, col_widths))
        print(line)


def getFilename():
    today = datetime.now().strftime("%Y-%m-%d")
    return f"weather_{today}.csv"


def writeToCsv(data):
    current_dir = os.path.dirname(__file__)
    filename = getFilename()
    file_path = os.path.join(current_dir, filename)
    file_exists = os.path.isfile(file_path)

    with open(filename, mode="a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)

        if not file_exists:
            writer.writerow(["City", "Temp [°C]", "Wind [km/h]"])
        for row in data:
            writer.writerow([row[0], row[1], row[2]])


async def main():
    cities = input("Enter city names separeted by spaces, commas or colons: ")
    cities = parseCityInput(cities)
    tasks = [processCity(city) for city in cities]
    results = await asyncio.gather(*tasks)

    printWeatherTable(results)

    if len(results) > 0:
        writeToCsv(results)


if __name__ == "__main__":
    asyncio.run(main())
