from flask import Flask, render_template, request, url_for, redirect
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg') 
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
import os

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost:3306/ventas'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


#ORM como hibernate como orientado a objetos
class Venta(db.Model):
    __tablename__ = 'ventas'  
    id = db.Column(db.Integer, primary_key=True)
    Fecha = db.Column(db.Date, nullable=False)
    Producto = db.Column(db.String(100), nullable=False)
    Ventas = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f"<Venta {self.Fecha} - {self.Producto}: {self.Ventas}>"

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        

        producto_seleccionado = request.form.get('producto')
        fecha_inicio = request.form.get('fecha_inicio')
        fecha_fin = request.form.get('fecha_fin')

       
        if not producto_seleccionado:
            error = "Por favor, seleccione un producto."
            return render_template('index.html', error=error)
        if not fecha_inicio or not fecha_fin:
            error = "Por favor, ingrese ambas fechas."
            return render_template('index.html', error=error)
        try:
            fecha_inicio = pd.to_datetime(fecha_inicio).date()
            fecha_fin = pd.to_datetime(fecha_fin).date()
        except ValueError:
            error = "Formato de fecha inválido. Use AAAA-MM-DD."
            return render_template('index.html', error=error)

        if fecha_inicio > fecha_fin:
            error = "La fecha de inicio no puede ser posterior a la fecha de fin."
            return render_template('index.html', error=error)

        # Obtener datos desde la base de datos según el rango y producto
        ventas_data = Venta.query.filter(
            Venta.Producto == producto_seleccionado,
            Venta.Fecha.between(fecha_inicio, fecha_fin)
        ).order_by(Venta.Fecha).all()

        if not ventas_data:
            error = "No hay datos de ventas disponibles para los criterios seleccionados."
            return render_template('index.html', error=error)

        # Crear DataFrame a partir de los datos obtenidos
        df = pd.DataFrame([{'Fecha': venta.Fecha, 'Producto': venta.Producto, 'Ventas': venta.Ventas} for venta in ventas_data])

        # Convertir la columna Fecha a tipo datetime
        df['Fecha'] = pd.to_datetime(df['Fecha'])

        # Generar promedio móvil de 3 días
        df['Promedio Movil'] = df['Ventas'].rolling(window=3).mean()

        # Calcular la variación de ventas
        df['Variación'] = df['Ventas'].diff()

        # Calcular el porcentaje de variación
        df['% Variación'] = df['Ventas'].pct_change() * 100

        # Interpretar la variación
        df['Interpretación'] = df['Variación'].apply(lambda x: 'Aumenta' if x > 0 else ('Disminuye' if x < 0 else 'No cambia'))

        # Preparar datos para un modelo predictivo
        df['Fecha_Ordinal'] = df['Fecha'].map(lambda x: x.toordinal())
        X = df[['Fecha_Ordinal']]
        y = df['Ventas']

        # Entrenar un modelo de regresión lineal
        modelo = LinearRegression()
        modelo.fit(X, y)

        # Predicción para los próximos 15 días
        dias_a_predecir = 15
        ultima_fecha = df['Fecha'].iloc[-1]
        fechas_futuras = pd.date_range(start=ultima_fecha + pd.Timedelta(days=1), periods=dias_a_predecir, freq='D')
        fechas_futuras_ordinales = np.array([fecha.toordinal() for fecha in fechas_futuras]).reshape(-1, 1)

        # Predicción de ventas para los próximos días
        predicciones = modelo.predict(fechas_futuras_ordinales)

        # Crear DataFrame de predicciones
        df_predicciones = pd.DataFrame({
            'Fecha': fechas_futuras,
            'Predicción de Ventas': predicciones
        })

        # Calcular la variación y porcentaje de variación en las predicciones
        df_predicciones['Variación'] = df_predicciones['Predicción de Ventas'].diff()
        df_predicciones['% Variación'] = df_predicciones['Predicción de Ventas'].pct_change() * 100
        df_predicciones['Interpretación'] = df_predicciones['Variación'].apply(lambda x: 'Aumenta' if x > 0 else ('Disminuye' if x < 0 else 'No cambia'))

        # Calcular el cambio total en las predicciones
        cambio_total = df_predicciones['Predicción de Ventas'].iloc[-1] - df_predicciones['Predicción de Ventas'].iloc[0]
        porcentaje_cambio_total = ((df_predicciones['Predicción de Ventas'].iloc[-1] / df_predicciones['Predicción de Ventas'].iloc[0]) - 1) * 100

        if cambio_total > 0:
            enunciado = f"La predicción indica que las ventas aumentarán en un {porcentaje_cambio_total:.2f}% durante los próximos {dias_a_predecir} días."
        elif cambio_total < 0:
            enunciado = f"La predicción indica que las ventas disminuirán en un {abs(porcentaje_cambio_total):.2f}% durante los próximos {dias_a_predecir} días."
        else:
            enunciado = f"La predicción indica que las ventas se mantendrán sin cambios durante los próximos {dias_a_predecir} días."

        # Crear una gráfica de ventas históricas y predicciones
        plt.figure(figsize=(12,6))
        plt.plot(df['Fecha'], df['Ventas'], marker='o', label='Ventas Históricas')
        plt.plot(df_predicciones['Fecha'], df_predicciones['Predicción de Ventas'], marker='o', label='Predicciones Futuras')
        plt.xlabel('Fecha')
        plt.ylabel('Ventas')
        plt.title(f'Ventas Históricas y Predicciones Futuras - {producto_seleccionado}')
        plt.legend()
        plt.grid(True)

        # Guardar la gráfica en una carpeta estática
        if not os.path.exists('static'):
            os.makedirs('static')
        grafica_path = os.path.join('static', 'grafica_ventas.png')
        plt.savefig(grafica_path)
        plt.close()

        return render_template('index.html', enunciado=enunciado, df=df, df_predicciones=df_predicciones, image_path=grafica_path)
    else:
        # Método GET: mostrar el formulario
        # Obtener la lista de productos disponibles en la base de datos
        productos_disponibles = db.session.query(Venta.Producto).distinct().all()
        productos_disponibles = [p[0] for p in productos_disponibles]
        return render_template('index.html', productos=productos_disponibles)

if __name__ == '__main__':
    app.run(debug=True)