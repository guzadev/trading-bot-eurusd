# 📈 Bot de Trading EUR/USD - Rango Asiático + Ruptura + Reingreso + Cruce de EMA 21

Este bot está diseñado para complementar una estrategia de trading personal sobre el par **EUR/USD**, basada en la observación de **manipulaciones de mercado** por parte de operadores profesionales durante la apertura europea.

---

## 🎯 ¿Qué hace este bot?
  
Durante la **Asia Kill Zone** (entre 00:00 y 04:00 UTC), se forma un rango de consolidación que suele actuar como zona de interés institucional.
El bot entra en funcionamiento a partir de las **04:00 UTC hasta las 07:00 UTC**, monitoreando si el precio **rompe ese rango** y posteriormente **reingresa**. Lo que en algunos días de la semana suele indicar una **manipulación institucional clásica**.
Luego del reingreso, el bot evalúa el **cruce de la media móvil exponencial de 21 periodos (EMA 21)**. Este cruce puede señalar un **cambio de estructura del mercado**.
La combinación de **ruptura + reingreso + cruce de la EMA 21** conforma una secuencia técnica que puede indicar una **posible entrada** con mayor probabilidad de éxito.


📤 En cada evento clave, el bot envía una notificación por Telegram:
- 🚨 **Ruptura Alcista o Bajista**
- 🔄 **Reingreso al rango** (lo que usualmente precede a un movimiento de reversión)
- 🟢🔴 **Cruce de la EMA 21**: luego del reingreso, el bot monitorea la media móvil exponencial de 21 periodos (EMA 21). Si detecta un cruce técnico por cierre, envía un aviso

🛑 Una vez que detecta el reingreso, el bot **finaliza automáticamente**, evitando seguir haciendo consultas innecesarias.

---

## 🛰️ API utilizada

Este bot utiliza la API de datos históricos de [TraderMade](https://tradermade.com/) para obtener cotizaciones de EUR/USD en intervalos de 1 hora y 1 minuto.

---

## 📌 Caso real de uso personal

> *"Uso este bot como parte de mi rutina diaria de trading. A las 04:00 UTC arranca la acción europea, y a esa hora ya tengo definido el rango asiático. El bot me avisa si hay ruptura, y cuando reingresa, sé que hay una probabilidad de que se haya producido una manipulación típica del mercado (liquidez inducida o falsa ruptura). En ese momento me acerco a los gráficos para hacer un análisis manual: confirmo cambio de estructura y uso la media móvil como guía para una posible entrada."*

Este enfoque **me libera de estar frente al gráfico** todo el tiempo, y me permite actuar solo si ocurre un evento relevante.  
Es una herramienta de **alerta, no de ejecución automática**. El juicio final siempre es mío.

---

## 🕒 Horario de Funcionamiento

- Ejecuta **de lunes a viernes** de forma automática.
- Activo de **04:00 a 07:00 UTC**.
- Se apaga solo cuando detecta **Cruce de la EMA 21** o llega a las **07:00 UTC**.

---

## 🛠️ Estrategia detrás del bot

Este bot está diseñado para complementar una estrategia de trading **basada en manipulación de liquidez**, comúnmente aplicada al par **EUR/USD**, observada durante la apertura europea.

### ⚙️ Paso a paso de la estrategia:

- 📌 Se define la **"kill zone" asiática**: entre **00:00 y 04:00 UTC**
- 🧱 Se identifican el **máximo y mínimo** de ese rango utilizando velas de **1 hora**
- 🕓 A partir de las **04:00 UTC**, se baja a velas de **5 minutos** para:
  - Detectar una **ruptura del rango asiático**
  - Y luego, un posible **reingreso** al mismo
- 🔍 Tras el reingreso:
  - Se busca:
    - 📉 **Cambio de estructura**
    - 📈 **Confirmación con media móvil (EMA21)**
  - Esto permite evaluar si hay oportunidad de entrada **larga o corta**, según el caso

### 🎯 ¿Qué busca capturar esta estrategia?

- Evidencia de **engaño de liquidez institucional**.
- Un movimiento de falsa dirección generado en la apertura europea.
- La posterior **reversión con intención**, típica del comportamiento profesional.

Este bot **automatiza la vigilancia de los eventos clave**, pero **la entrada es discrecional**, ejecutada por el trader solo tras validación de su plan.

---

Desarrollado para uso personal. Código abierto por si querés adaptarlo a tu estilo. ¡Buen trading! 🧠📲
