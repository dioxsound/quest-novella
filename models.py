from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Scenario(db.Model):
    __tablename__ = 'scenarios'
    id = db.Column(db.Integer, primary_key=True)
    image = db.Column(db.String(255), nullable=True)
    text = db.Column(db.Text, nullable=False)
    
    # Отношение для выборов, связанных с этим сценарием
    choices = db.relationship(
        'Choice',
        backref='parent_scenario',
        lazy=True,
        foreign_keys='Choice.scenario_id'
    )
    
    # Отношение для выборов, которые ссылаются на этот сценарий как следующий сценарий
    next_choices = db.relationship(
        'Choice',
        backref='next_scenario',
        lazy=True,
        foreign_keys='Choice.next_scenario_id'
    )

class Choice(db.Model):
    __tablename__ = 'choices'
    id = db.Column(db.Integer, primary_key=True)
    
    # Внешний ключ на сценарий, к которому относится выбор
    scenario_id = db.Column(db.Integer, db.ForeignKey('scenarios.id'), nullable=False)
    
    # Внешний ключ на следующий сценарий (может быть NULL)
    next_scenario_id = db.Column(db.Integer, db.ForeignKey('scenarios.id'), nullable=True)
    
    choice_text = db.Column(db.String(255), nullable=False)
