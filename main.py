import re
import asyncio
import httpx


async def fetchGeocode(city):
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


async def fetchWeather(lat, lon):
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(url)
        data = resp.json()
        return data


async def processCity(city):
    geo = await fetchGeocode(city)

    if not geo["error"]:
        weather = await fetchWeather(geo["latitude"], geo["longitude"])
        return weather
    return {"error": True, "city": city}


def parseCityInput(input_str):
    cities = re.split(r"\s*[,:\s]\s*", input_str.strip())
    return [city for city in cities if city]


async def main():
    cities = input("Enter city names separeted by spaces, commas or colons: ")
    cities = parseCityInput(cities)
    tasks = [processCity(city) for city in cities]

    results = await asyncio.gather(*tasks)

    for res in results:
        print(res)


if __name__ == "__main__":
    asyncio.run(main())
