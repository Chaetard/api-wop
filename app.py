# app.py

from flask import Flask, render_template
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression

app = Flask(__name__)

@app.route('/')
def index():
    # Datos de ejemplo: producto, fechas y ventas fluctuantes
    np.random.seed(42)  # Para asegurar la reproducibilidad de los datos

    # Fechas (20 días)
    fechas = pd.date_range(start="2024-12-01", periods=20, freq="D")

    # Crear ventas fluctuantes para un producto
    ventas_producto = np.random.randint(60, 120, size=20) + np.random.randint(-15, 15, size=20)

    # Datos del DataFrame
    data = {
        'Fecha': fechas,
        'Producto': ['Producto A'] * 20,
        'Ventas': ventas_producto
    }

    # Crear DataFrame
    df = pd.DataFrame(data)

    # Convertir la columna Fecha a tipo datetime
    df['Fecha'] = pd.to_datetime(df['Fecha'])

    # Generar promedio móvil de 3 días
    df['Promedio Movil'] = df['Ventas'].rolling(window=3).mean()

    # Calcular la variación de ventas
    df['Variación'] = df['Ventas'].diff()  # Calcula la diferencia entre ventas consecutivas

    # Interpretar la variación
    df['Interpretación'] = df['Variación'].apply(lambda x: 'Aumenta' if x > 0 else ('Disminuye' if x < 0 else 'No cambia'))

    # Preparar datos para un modelo predictivo simple
    df['Fecha_Ordinal'] = df['Fecha'].map(lambda x: x.toordinal())  # Convertir fechas a ordinales
    X = df[['Fecha_Ordinal']]  # Variable independiente
    y = df['Ventas']           # Variable dependiente

    # Entrenar un modelo de regresión lineal
    modelo = LinearRegression()
    modelo.fit(X, y)

    # Aquí simulamos que estamos en el 20 de diciembre y queremos predecir ventas para los próximos 10 días
    fecha_actual = pd.to_datetime('2024-12-20')

    # Generar las próximas fechas para predecir ventas (por ejemplo, 10 días futuros)
    futuras_fechas = pd.date_range(start=fecha_actual, periods=11, freq='D')[1:]  # Los próximos 10 días

    # Convertir las fechas futuras a valores ordinales
    futuras_ordinales = np.array([fecha.toordinal() for fecha in futuras_fechas]).reshape(-1, 1)

    # Predicción de ventas para los próximos 10 días
    predicciones = modelo.predict(futuras_ordinales)

    # Crear DataFrame de predicciones
    df_predicciones = pd.DataFrame({'Fecha': futuras_fechas, 'Predicción de Ventas': predicciones})

    return render_template('index.html', df=df, df_predicciones=df_predicciones)

if __name__ == '__main__':
    app.run(debug=True)