# Marshmallow schemas for Task and Category with:
# - Validation for title and description length
# - Validation for due_date format
from marshmallow import fields, validate
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from app.models import TaskModel, CategoryModel

# Marshmallow schema for Category with validation and task count
class CategorySchema(SQLAlchemyAutoSchema):
    class Meta:
        model = CategoryModel
        load_instance = False
        name = "CategoryItem"

    name = fields.String(required=True, validate=validate.Length(min=1, max=50))
    color = fields.String(validate=validate.Regexp(r'^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$'), allow_none=True)
    task_count = fields.Function(lambda obj: len(obj.tasks) if obj.tasks else 0)

# Marshmallow schema for Task with validation and nested category
class TaskSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = TaskModel
        load_instance = False
        name = "TaskItem"

    title = fields.String(required=True, validate=validate.Length(min=1, max=100))
    description = fields.String(validate=validate.Length(max=500), allow_none=True)
    completed = fields.Boolean(allow_none=True)
    due_date = fields.DateTime(format='iso', allow_none=True)
    category_id = fields.Integer(allow_none=True)



