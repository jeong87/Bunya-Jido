from dataclasses import dataclass


@dataclass(frozen=True)
class ForecastOptions:
    city: str
    units: str = "metric"


@dataclass(frozen=True)
class Forecast:
    city: str
    temperature: float
    units: str


class HttpTransport:
    def get_forecast(self, options: ForecastOptions) -> Forecast:
        return Forecast(city=options.city, temperature=20.0, units=options.units)


class WeatherClient:
    def __init__(self, transport: HttpTransport) -> None:
        self.transport = transport

    def forecast(self, options: ForecastOptions) -> Forecast:
        return self.transport.get_forecast(options)
