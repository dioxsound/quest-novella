from flask import Flask, render_template, redirect, url_for, request, flash
from config import Config
from models import db, Scenario, Choice
from forms import ScenarioForm, ChoiceForm
from flask_migrate import Migrate
import os
import uuid
from werkzeug.utils import secure_filename
from PIL import Image
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
app.config.from_object(Config)

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
db.init_app(app)
migrate = Migrate(app, db)

UPLOAD_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'static', 'images')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

MAX_IMAGE_WIDTH = 800
MAX_IMAGE_HEIGHT = 600

def resize_image(image_path):
    try:
        with Image.open(image_path) as img:
            img = img.convert('RGB')
            img.thumbnail((MAX_IMAGE_WIDTH, MAX_IMAGE_HEIGHT))
            img.save(image_path)
    except Exception as e:
        print(f"Ошибка при изменении размера изображения: {e}")


@app.context_processor
def inject_theme():
    dark_mode = request.cookies.get('dark_mode') == 'true'
    return dict(dark_mode=dark_mode)

@app.route('/')
def index():
    start_scenarios = Scenario.query.filter_by(is_start=True).all()
    return render_template('index.html', start_scenarios=start_scenarios)

@app.route('/scenario/<int:scenario_id>')
def show_scenario(scenario_id):
    scenario = Scenario.query.get_or_404(scenario_id)
    return render_template('scenario.html', scenario=scenario)

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
        if form.image.data and form.image.data.filename:
            image = form.image.data
            ext = os.path.splitext(image.filename)[1].lower()
            if ext in ['.jpg', '.jpeg', '.png']:
                filename = f"{uuid.uuid4().hex}{ext}"
                image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                image.save(image_path)
                resize_image(image_path)
                image_filename = filename
            else:
                flash('Файл изображения должен быть в формате JPG, JPEG или PNG.', 'danger')
                return redirect(request.url)
        
        new_scenario = Scenario(
            text=form.text.data,
            image=image_filename,
            is_start=form.is_start.data
        )
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
        scenario.is_start = form.is_start.data
        if form.image.data and form.image.data.filename:
            image = form.image.data
            ext = os.path.splitext(image.filename)[1].lower()
            if ext in ['.jpg', '.jpeg', '.png']:
                filename = f"{uuid.uuid4().hex}{ext}"
                image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                image.save(image_path)
                resize_image(image_path)
                scenario.image = filename
            else:
                flash('Файл изображения должен быть в формате JPG, JPEG или PNG.', 'danger')
                return redirect(request.url)
        

        db.session.commit()
        flash('Сценарий обновлен успешно!', 'success')
        return redirect(url_for('admin'))
    return render_template('edit_scenario.html', form=form, scenario=scenario)

# Остальные маршруты delete_choice, delete_scenario, create_choice, edit_choice — без изменений

@app.route('/toggle_theme')
def toggle_theme():
    dark_mode = request.cookies.get('dark_mode') == 'true'
    dark_mode = not dark_mode
    response = redirect(request.referrer or url_for('index'))
    response.set_cookie('dark_mode', 'true' if dark_mode else 'false', max_age=30*24*60*60)
    return response
@app.route('/admin/create_choice', methods=['GET', 'POST'])
def create_choice():
    form = ChoiceForm()

    # ВСЕГДА подгружаем варианты сценариев
    scenarios = Scenario.query.all()
    form.scenario.choices = [(s.id, f"ID {s.id}: {s.text[:50]}") for s in scenarios]
    form.next_scenario.choices = [(0, 'Конец игры')] + [(s.id, f"ID {s.id}: {s.text[:50]}") for s in scenarios]

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
@app.route('/admin/delete_scenario/<int:scenario_id>', methods=['POST'])
def delete_scenario(scenario_id):
    scenario = Scenario.query.get_or_404(scenario_id)
    # Удаляем связанные выборы
    Choice.query.filter_by(scenario_id=scenario_id).delete()
    db.session.delete(scenario)
    db.session.commit()
    flash('Сценарий удален успешно!', 'success')
    return redirect(url_for('admin'))

if __name__ == '__main__':
    app.run(debug=True)
