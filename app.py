from flask import Flask, render_template, redirect, url_for, request, flash
from config import Config
from models import db, Scenario, Choice
from forms import ScenarioForm, ChoiceForm
from flask_migrate import Migrate
import os
from werkzeug.utils import secure_filename
from PIL import Image
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
app.config.from_object(Config)

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')

db.init_app(app)
migrate = Migrate(app, db)

# Папка для загруженных изображений
UPLOAD_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'static', 'images')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Максимальный размер изображения (например, 800x600)
MAX_IMAGE_WIDTH = 800
MAX_IMAGE_HEIGHT = 600

def resize_image(image_path):
    with Image.open(image_path) as img:
        img = img.convert('RGB')
        img.thumbnail((MAX_IMAGE_WIDTH, MAX_IMAGE_HEIGHT))
        img.save(image_path)

@app.context_processor
def inject_theme():
    dark_mode = request.cookies.get('dark_mode') == 'true'
    return dict(dark_mode=dark_mode)

@app.route('/')
def index():
    scenario = Scenario.query.first()
    return render_template('index.html', scenario=scenario)

@app.route('/scenario/<int:scenario_id>')
def show_scenario(scenario_id):
    scenario = Scenario.query.get_or_404(scenario_id)
    return render_template('index.html', scenario=scenario)

@app.route('/admin')
def admin():
    scenarios = Scenario.query.all()
    choices = Choice.query.all()
    return render_template('admin.html', scenarios=scenarios, choices=choices)

@app.route('/admin/create_scenario', methods=['GET', 'POST'])
def create_scenario():
    form = ScenarioForm()
    if form.validate_on_submit():
        image_filename = None
        if form.image.data:
            image = form.image.data
            filename = secure_filename(image.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image.save(image_path)
            resize_image(image_path)
            image_filename = filename
        new_scenario = Scenario(text=form.text.data, image=image_filename)
        db.session.add(new_scenario)
        db.session.commit()
        flash('Сценарий создан успешно!', 'success')
        return redirect(url_for('admin'))
    return render_template('create_scenario.html', form=form)

@app.route('/admin/edit_scenario/<int:scenario_id>', methods=['GET', 'POST'])
def edit_scenario(scenario_id):
    scenario = Scenario.query.get_or_404(scenario_id)
    form = ScenarioForm(obj=scenario)
    if form.validate_on_submit():
        scenario.text = form.text.data
        if form.image.data:
            image = form.image.data
            filename = secure_filename(image.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image.save(image_path)
            resize_image(image_path)
            scenario.image = filename
        db.session.commit()
        flash('Сценарий обновлен успешно!', 'success')
        return redirect(url_for('admin'))
    return render_template('edit_scenario.html', form=form, scenario=scenario)

@app.route('/admin/delete_scenario/<int:scenario_id>', methods=['POST'])
def delete_scenario(scenario_id):
    scenario = Scenario.query.get_or_404(scenario_id)
    # Удаляем связанные выборы
    Choice.query.filter_by(scenario_id=scenario_id).delete()
    db.session.delete(scenario)
    db.session.commit()
    flash('Сценарий удален успешно!', 'success')
    return redirect(url_for('admin'))

@app.route('/admin/create_choice', methods=['GET', 'POST'])
def create_choice():
    form = ChoiceForm()
    form.scenario.choices = [(s.id, f"ID {s.id}: {s.text[:50]}") for s in Scenario.query.all()]
    form.next_scenario.choices = [(0, 'Конец игры')] + [(s.id, f"ID {s.id}: {s.text[:50]}") for s in Scenario.query.all()]
    if form.validate_on_submit():
        next_scenario_id = form.next_scenario.data if form.next_scenario.data != 0 else None
        new_choice = Choice(
            scenario_id=form.scenario.data,
            choice_text=form.choice_text.data,
            next_scenario_id=next_scenario_id
        )
        db.session.add(new_choice)
        db.session.commit()
        flash('Выбор создан успешно!', 'success')
        return redirect(url_for('admin'))
    return render_template('create_choice.html', form=form)

@app.route('/admin/edit_choice/<int:choice_id>', methods=['GET', 'POST'])
def edit_choice(choice_id):
    choice = Choice.query.get_or_404(choice_id)
    form = ChoiceForm(obj=choice)
    form.scenario.choices = [(s.id, f"ID {s.id}: {s.text[:50]}") for s in Scenario.query.all()]
    form.next_scenario.choices = [(0, 'Конец игры')] + [(s.id, f"ID {s.id}: {s.text[:50]}") for s in Scenario.query.all()]
    if form.validate_on_submit():
        choice.scenario_id = form.scenario.data
        choice.choice_text = form.choice_text.data
        choice.next_scenario_id = form.next_scenario.data if form.next_scenario.data != 0 else None
        db.session.commit()
        flash('Выбор обновлен успешно!', 'success')
        return redirect(url_for('admin'))
    form.next_scenario.data = choice.next_scenario_id if choice.next_scenario_id else 0
    return render_template('edit_choice.html', form=form, choice=choice)

@app.route('/admin/delete_choice/<int:choice_id>', methods=['POST'])
def delete_choice(choice_id):
    choice = Choice.query.get_or_404(choice_id)
    db.session.delete(choice)
    db.session.commit()
    flash('Выбор удален успешно!', 'success')
    return redirect(url_for('admin'))

@app.route('/toggle_theme')
def toggle_theme():
    # Простая реализация переключения темы с использованием сессий
    dark_mode = request.cookies.get('dark_mode') == 'true'
    dark_mode = not dark_mode
    response = redirect(request.referrer or url_for('index'))
    response.set_cookie('dark_mode', 'true' if dark_mode else 'false', max_age=30*24*60*60)  # 30 дней
    return response

if __name__ == '__main__':
    app.run(debug=True)
