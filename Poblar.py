from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
import numpy as np
import random
import os

app = Flask(__name__)

# Configuración de la base de datos con MySQL
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost:3306/ventas'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Definir el modelo de datos
class Venta(db.Model):
    __tablename__ = 'ventas'
    id = db.Column(db.Integer, primary_key=True)
    Fecha = db.Column(db.Date, nullable=False)
    Producto = db.Column(db.String(100), nullable=False)
    Ventas = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f"<Venta {self.Fecha} - {self.Producto}: {self.Ventas}>"

def poblar_base_de_datos():
    with app.app_context():
        # Crear las tablas (si no existen)
        db.create_all()

        # Verificar si ya hay datos en la tabla
        registros_existentes = Venta.query.count()
        if registros_existentes >= 5000:
            print("La base de datos ya contiene 5000 o más registros.")
            return
        else:
            print(f"La tabla actualmente tiene {registros_existentes} registros. Agregando datos...")

        # Configuración para generar datos
        numero_registros = 5000 - registros_existentes
        productos = ['Producto A', 'Producto B', 'Producto C', 'Producto D']
        fecha_inicio = pd.to_datetime('2021-01-01')
        fecha_fin = pd.to_datetime('2025-02-28')
        dias_totales = (fecha_fin - fecha_inicio).days + 1

        # Generar fechas aleatorias
        fechas_aleatorias = [fecha_inicio + pd.Timedelta(days=random.randint(0, dias_totales - 1)) for _ in range(numero_registros)]

        # Generar ventas aleatorias y realistas
        ventas_aleatorias = []
        for _ in range(numero_registros):
            venta = max(0, np.random.normal(loc=200, scale=50))
            ventas_aleatorias.append(round(venta, 2))

        # Seleccionar productos aleatoriamente
        productos_aleatorios = [random.choice(productos) for _ in range(numero_registros)]

        # Crear registros y agregarlos a la sesión
        registros = []
        for fecha, producto, venta in zip(fechas_aleatorias, productos_aleatorios, ventas_aleatorias):
            nueva_venta = Venta(Fecha=fecha.date(), Producto=producto, Ventas=venta)
            registros.append(nueva_venta)

        db.session.bulk_save_objects(registros)
        db.session.commit()
        print(f"Se han agregado {len(registros)} registros a la base de datos.")

if __name__ == '__main__':
    poblar_base_de_datos()