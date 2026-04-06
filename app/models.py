# SQLAlchemy models for Task and Category with relationships and timestamps

from app import db
from datetime import datetime, timezone

# SQLAlchemy model for Task
class TaskModel(db.Model):
    __tablename__ = "tasks"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    completed = db.Column(db.Boolean, default=False)
    due_date = db.Column(db.DateTime, nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))

    # Create the database relationship to CategoryModel
    category = db.relationship('CategoryModel', back_populates='tasks')

    # Method to convert TaskModel instance to dictionary
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'completed': self.completed,
            'due_date': self.due_date,
            'category_id': self.category_id,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
    
# SQLAlchemy model for Category
class CategoryModel(db.Model):
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    color = db.Column(db.String(7), nullable=True)

    # Create the database relationship to TaskModel
    tasks = db.relationship('TaskModel', back_populates='category')

    # Method to convert CategoryModel instance to dictionary, including task count
    def to_dict(self):
        cnt = len(self.tasks) if self.tasks else 0
        return {
            'id': self.id,
            'name': self.name,
            'color': self.color,
            'task_count': cnt,
            'tasks':  self.tasks
        }
