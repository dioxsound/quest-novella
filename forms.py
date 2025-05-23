from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, SelectField, FileField, BooleanField
from wtforms.validators import DataRequired, InputRequired
from flask_wtf.file import FileAllowed

class ScenarioForm(FlaskForm):
    text = TextAreaField('Текст сценария', validators=[DataRequired()], render_kw={"id": "text"})
    image = FileField('Изображение', validators=[FileAllowed(['jpg', 'png', 'jpeg'], 'Только изображения!')])
    is_start = BooleanField('Это начало новой игры?')
    submit = SubmitField('Сохранить')

class ChoiceForm(FlaskForm):
    scenario = SelectField('Сценарий', coerce=int, validators=[DataRequired()])
    choice_text = StringField('Текст выбора', validators=[DataRequired()])
    next_scenario = SelectField('Следующий сценарий', coerce=int, choices=[], validators=[InputRequired()])
    submit = SubmitField('Сохранить')
