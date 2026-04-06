# Category endpoints

from flask import jsonify
from flask.views import MethodView
from flask_smorest import Blueprint, abort
from sqlalchemy.orm import joinedload

from app import db
from app.models import CategoryModel
from ..schemas import CategorySchema, TaskSchema

categories_blp = Blueprint("categories", __name__, description="Operations on categories")

def handle_errors(err, error_code=400):
    # Flask-Smorest marshmallow validation attaches errors in err.data or err.description.
    errors = None
    if hasattr(err, "data") and err.data:
        if isinstance(err.data, dict):
            errors = err.data.get("json") or err.data.get("messages") or err.data
    if not errors and hasattr(err, "description"):
        errors = err.description

    if isinstance(errors, dict) and "json" in errors:
        errors = errors["json"]

    if errors is None:
        errors = "Unprocessable Entity"

    return jsonify({"errors": errors}), error_code

@categories_blp.errorhandler(422)
def handle_error_422(err):
    return handle_errors(err, error_code=400)

@categories_blp.errorhandler(400)
def handle_error_400(err):
    return handle_errors(err, error_code=400)


@categories_blp.route("/categories")
class CategoryList(MethodView):
    # GET /categories: Returns all categories with the count of tasks in each.
    @categories_blp.response(200, CategorySchema(many=True))
    def get(self):
        """Get all categories."""

        query = CategoryModel.query
        categories = query.options(joinedload(CategoryModel.tasks)).all()
        cat_schema = CategorySchema(many=True, only=["id", "name", "color", "task_count"])
        serialized_cats = cat_schema.dump(categories)
        return jsonify({"categories": serialized_cats})


    # POST /categories: Creates a new category.
    @categories_blp.arguments(CategorySchema)
    def post(self, category_data):
        """Create a new category."""
        if CategoryModel.query.filter_by(name=category_data["name"]).first():
            abort(400, message="Category with this name already exists")

        category = CategoryModel(
            name=category_data["name"], 
            color=category_data.get("color")
        )

        try:
            db.session.add(category)
            db.session.commit()
        except Exception:
            db.session.rollback()
            abort(400, message="Failed to create category")

        cat_schema = CategorySchema(many=False)
        serialized_category = cat_schema.dump(category)
        return jsonify(serialized_category), 201


@categories_blp.route("/categories/<int:category_id>")
class Category(MethodView):
    # GET /categories/:id: Returns a single category with its tasks.
    def get(self, category_id):
        """Get a specific category."""
        query = CategoryModel.query.filter_by(id=category_id)

        category_dict = query.options(joinedload(CategoryModel.tasks)).first()
        if not category_dict:
            abort(404, message="Category not found")
        try:

            task_schema = TaskSchema(many=True, only=["id", "title", "completed"])
            serialized_tasks = task_schema.dump(category_dict.tasks)
            serialized_category = {
                "id": category_dict.id,
                "name": category_dict.name,
                "color": category_dict.color,
                "tasks": serialized_tasks
            }
            return jsonify(serialized_category)
        except Exception:
            abort(400, message="Failed to retrieve category")

    # PUT /categories/:id: Updates an existing category with validation.
    @categories_blp.arguments(CategorySchema)
    @categories_blp.response(200, CategorySchema)
    def put(self, category_data, category_id):
        """Update a category."""

        category = CategoryModel.query.get(category_id)
        # Check if category exists
        if not category:
            abort(404, message="Category not found")

        category.name = category_data.get('name', category.name)
        category.color = category_data.get('color', category.color)

        # Check if new name is unique (if name is being updated)
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            abort(400, message="Failed to update category")

        cat_schema = CategorySchema(many=False)
        serialized_category = cat_schema.dump(category)
        return jsonify(serialized_category), 201
    
    # DELETE /categories/:id: Deletes a category. Cannot delete a category that has tasks.
    def delete(self, category_id):
        """Delete a category."""
        category = CategoryModel.query.get(category_id)
        # Check if category exists
        if not category:
            abort(404, message="Category not found")

        # Check if category has tasks
        if category.tasks and len(category.tasks) > 0:
            abort(400, message="Cannot delete category with existing tasks. Move or delete tasks first.")

        try:
            db.session.delete(category)
            db.session.commit()
        except Exception:
            db.session.rollback()
            abort(400, message="Failed to delete category")

        return {"message": "Category deleted"}, 200
    
