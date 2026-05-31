# Acorn Weather SDK

`WeatherClient.forecast(options)` is the public caller surface. It receives
`ForecastOptions`, delegates transport details to `HttpTransport`, and exposes
a typed `Forecast` result.

This miniature is read as a client contract, not as a captured network
request. Its Studio tour is a structural walk through public API, caller
options, transport boundary, and returned model.
