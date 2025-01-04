from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SelectField
from wtforms.validators import InputRequired, Length, ValidationError

# Crear la instancia de la aplicación Flask
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'supersecretkey'

# Crear la instancia de la base de datos
db = SQLAlchemy(app)

# Configurar Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Definición de modelos
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    vehicles = db.relationship('Vehicle', backref='client', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'phone': self.phone,
            'email': self.email,
            'address': self.address
        }

class Vehicle(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    model = db.Column(db.String(100), nullable=False)
    brand = db.Column(db.String(100), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    license_plate = db.Column(db.String(10), nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'model': self.model,
            'brand': self.brand,
            'year': self.year,
            'license_plate': self.license_plate,
            'client': self.client.to_dict()
        }

# Formularios de Flask-WTF
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired(), Length(min=4, max=150)])
    password = PasswordField('Password', validators=[InputRequired(), Length(min=4, max=150)])
    remember = BooleanField('Remember me')

class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired(), Length(min=4, max=150)])
    password = PasswordField('Password', validators=[InputRequired(), Length(min=4, max=150)])

    def validate_username(self, username):
        existing_user = User.query.filter_by(username=username.data).first()
        if existing_user:
            raise ValidationError('Username already exists.')

# Cargar usuario
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Rutas de autenticación
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            return redirect(url_for('vehicle_reception'))
        flash('Invalid username or password')
    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
@login_required
def register():
    if not current_user.is_admin:
        return redirect(url_for('vehicle_reception'))
    form = RegisterForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data, method='sha256')
        new_user = User(username=form.username.data, password=hashed_password, is_admin=False)
        db.session.add(new_user)
        db.session.commit()
        flash('User created successfully')
        return redirect(url_for('vehicle_reception'))
    return render_template('register.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# Rutas de la aplicación
@app.route('/')
@login_required
def vehicle_reception():
    clients = Client.query.all()
    vehicles = Vehicle.query.all()
    return render_template('vehicle_reception.html', clients=clients, vehicles=vehicles)
    
@app.route('/receptions', methods=['GET', 'POST'])
@login_required
def receptions():
    if request.method == 'POST':
        search_term = request.form['search']
        receptions = Vehicle.query.filter(Vehicle.license_plate.contains(search_term)).all()
    else:
        receptions = Vehicle.query.all()
    
    return render_template('receptions.html', receptions=[reception.to_dict() for reception in receptions])    
    
@app.route('/update_reception', methods=['POST'])
@login_required
def update_reception():
    data = request.json
    reception_id = data['id']
    reception = Vehicle.query.get(reception_id)
    if reception:
        reception.license_plate = data['license_plate']
        reception.model = data['model']
        reception.brand = data['brand']
        reception.year = data['year']
        reception.client.name = data['client']['name']
        db.session.commit()
    return jsonify(success=True)

@app.route('/add_client', methods=['GET', 'POST'])
@login_required
def add_client():
    if request.method == 'POST':
        name = request.form['name']
        phone = request.form['phone']
        email = request.form['email']
        address = request.form['address']
        
        client = Client(name=name, phone=phone, email=email, address=address)
        db.session.add(client)
        db.session.commit()
        
        return redirect(url_for('vehicle_reception'))
    
    return render_template('add_client.html')

@app.route('/add_vehicle', methods=['GET', 'POST'])
@login_required
def add_vehicle():
    if request.method == 'POST':
        model = request.form['model']
        brand = request.form['brand']
        year = request.form['year']
        license_plate = request.form['license_plate']
        client_id = request.form['client_id']
        
        vehicle = Vehicle(model=model, brand=brand, year=year, license_plate=license_plate, client_id=client_id)
        db.session.add(vehicle)
        db.session.commit()
        
        return redirect(url_for('vehicle_reception'))
    
    return render_template('add_vehicle.html')

@app.route('/view_vehicles')
@login_required
def view_vehicles():
    vehicles = Vehicle.query.all()
    return render_template('view_vehicles.html', vehicles=vehicles)

@app.route('/manage_users')
@login_required
def manage_users():
    if not current_user.is_admin:
        return redirect(url_for('vehicle_reception'))
    users = User.query.all()
    return render_template('manage_users.html', users=users)

@app.route('/delete_user/<int:id>')
@login_required
def delete_user(id):
    if not current_user.is_admin:
        return redirect(url_for('vehicle_reception'))
    user = User.query.get(id)
    if user:
        db.session.delete(user)
        db.session.commit()
        flash('User deleted successfully')
    return redirect(url_for('manage_users'))

# Rutas para búsqueda
@app.route('/search_client', methods=['POST'])
@login_required
def search_client():
    client_name = request.form['client_search']
    client = Client.query.filter_by(name=client_name).first()
    if client:
        flash(f'Cliente encontrado: {client.name}, Teléfono: {client.phone}')
    else:
        flash('Cliente no encontrado')
    return redirect(url_for('vehicle_reception'))

@app.route('/search_vehicle', methods=['POST'])
@login_required
def search_vehicle():
    vehicle_plate = request.form['vehicle_search']
    vehicle = Vehicle.query.filter_by(license_plate=vehicle_plate).first()
    if vehicle:
        flash(f'Vehículo encontrado: {vehicle.brand} {vehicle.model}, Año: {vehicle.year}')
    else:
        flash('Vehículo no encontrado')
    return redirect(url_for('vehicle_reception'))

# Crear las tablas de la base de datos y ejecutar la aplicación
if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Crear las tablas en la base de datos
        # Crear un usuario administrador si no existe
        if not User.query.filter_by(username='admin').first():
            admin_user = User(username='admin', password=generate_password_hash('admin', method='sha256'), is_admin=True)
            db.session.add(admin_user)
            db.session.commit()
    app.run(debug=True)  # Ejecutar la aplicación en modo de depuración