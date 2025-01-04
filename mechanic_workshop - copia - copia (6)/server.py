from flask import Flask, render_template, request, jsonify, url_for
from datetime import datetime

app = Flask(__name__)

# Ejemplo de datos de recepciones
class Vehicle:
    def __init__(self, id, license_plate, model, brand, year, client):
        self.id = id
        self.license_plate = license_plate
        self.model = model
        self.brand = brand
        self.year = year
        self.client = client

    def to_dict(self):
        return {
            'id': self.id,
            'license_plate': self.license_plate,
            'model': self.model,
            'brand': self.brand,
            'year': self.year,
            'client': self.client.to_dict()
        }

class Client:
    def __init__(self, name):
        self.name = name

    def to_dict(self):
        return {
            'name': self.name
        }

# Datos de ejemplo
clients = [Client(name='John Doe'), Client(name='Jane Smith')]
receptions = [
    Vehicle(1, 'ABC123', 'Corolla', 'Toyota', 2020, clients[0]),
    Vehicle(2, 'XYZ789', 'Civic', 'Honda', 2021, clients[1]),
    Vehicle(3, 'LMN456', 'Focus', 'Ford', 2022, clients[0])
]

@app.route('/receptions', methods=['GET', 'POST'])
def receptions():
    if request.method == 'POST':
        search = request.form.get('search')
        filtered_receptions = [reception.to_dict() for reception in receptions if search.lower() in reception.license_plate.lower()]
        return render_template('receptions.html', receptions=filtered_receptions)
    return render_template('receptions.html', receptions=[reception.to_dict() for reception in receptions])

@app.route('/update_reception', methods=['POST'])
def update_reception():
    data = request.json
    reception_id = data['id']
    reception = next((r for r in receptions if r.id == reception_id), None)
    if reception:
        reception.license_plate = data['license_plate']
        reception.model = data['model']
        reception.brand = data['brand']
        reception.year = data['year']
        reception.client.name = data['client']['name']
    return jsonify(success=True)

if __name__ == '__main__':
    app.run(debug=True)