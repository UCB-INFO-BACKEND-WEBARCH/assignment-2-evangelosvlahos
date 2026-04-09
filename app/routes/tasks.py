# Task endpoints

import json
from flask import request, jsonify
from flask.views import MethodView
from flask_smorest import Blueprint, abort
from sqlalchemy.orm import joinedload
from datetime import datetime, timedelta, timezone

from app import db
from ..models import TaskModel, CategoryModel
from ..schemas import TaskSchema
from ..jobs import send_due_date_reminder

tasks_blp = Blueprint("tasks", __name__, description="Operations on tasks")

def handle_errors(err, error_code=400):
    # Flask-Smorest marshmallow validation attaches errors in err.data or err.description.
    errors = None
    # Check for errors in the attribute 'data' of the error object
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

@tasks_blp.errorhandler(422)
def handle_error_422(err):
    return handle_errors(err, error_code=400)

@tasks_blp.errorhandler(400)
def handle_error_400(err):
    return handle_errors(err, error_code=400)



@tasks_blp.route("/tasks")
class TaskList(MethodView):
    # GET /tasks: Returns a list of all tasks.
    def get(self):
        """Get all tasks, with optional filters."""
        category_id = request.args.get('category_id')
        completed_str = request.args.get('completed')

        query = TaskModel.query

        if category_id:
            try:
                category_id = int(category_id)
            except ValueError:
                abort(400, message="Invalid category_id")
            query = query.filter_by(category_id=category_id)

        if completed_str is not None:
            try:
                completed_value = json.loads(completed_str)
                if not isinstance(completed_value, bool):
                    abort(400, message="Invalid completed value. Must be a boolean.")
            except (ValueError, json.JSONDecodeError):
                abort(400, message="Invalid completed value. Must be a boolean.")
            query = query.filter_by(completed=completed_value)

        tasks = query.options(joinedload(TaskModel.category)).all()
        task_schema = TaskSchema(many=True)
        serialized_tasks = task_schema.dump(tasks)
        return jsonify({"tasks": serialized_tasks})

    # POST /tasks: Creates a new task with validation.
    @tasks_blp.arguments(TaskSchema)
    @tasks_blp.response(201, TaskSchema)
    def post(self, task_data):
        """Create a new task."""

        if task_data.get('category_id'):
            category = CategoryModel.query.get(task_data['category_id'])
            if not category:
                abort(400, message="Category not found")

        time_until_due = None
        due_date = task_data.get('due_date')
        if due_date:
            if isinstance(due_date, str):
                try:
                    due_date = datetime.fromisoformat(due_date.replace('Z', '+00:00'))
                    task_data['due_date'] = due_date
                except ValueError:
                    abort(400, message="Invalid due_date format. Must be ISO 8601 string.")
            now = datetime.now(timezone.utc) if due_date.tzinfo else datetime.now()
            time_until_due = due_date - now

        try:
            task = TaskModel(**task_data)
            db.session.add(task)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            abort(400, message="Failed to create task")

        
        # Queue notification if due date is in the future and within 24 hours
        notified = False

        if time_until_due and time_until_due > timedelta(0) and time_until_due <= timedelta(hours=24):
            try:
                send_due_date_reminder.delay(task.title)
                notified = True
            except Exception as e:
                # Log the error but don't fail the task creation
                print(f"Failed to queue notification: {e}")

        task_schema = TaskSchema(many=False)
        serialized_task = task_schema.dump(task)
        serialized_task_with_notify = jsonify(serialized_task)
        return jsonify({
            "task": serialized_task_with_notify.get_json(),
            "notification_queued": notified
        }), 201


@tasks_blp.route("/tasks/<int:task_id>")
class Task(MethodView):

    # GET /tasks/:id: Returns a single task with its category information.
    @tasks_blp.response(200, TaskSchema)
    def get(self, task_id):
        """Get a specific task."""

        task = TaskModel.query.options(joinedload(TaskModel.category)).get(task_id)
        if not task:
            abort(404, message="Task not found")

        task_schema = TaskSchema()
        serialized_task = task_schema.dump(task)
        return jsonify(serialized_task), 200


    # PUT /tasks/:id: Updates an existing task with validation.
    @tasks_blp.arguments(schema=TaskSchema(partial=True))
    @tasks_blp.response(200, schema=None)
    def put(self, task_data, task_id):
        """Update a task."""
        
        # Create a query to get the task and its category (if any)
        task = TaskModel.query.get(task_id)
        # Check if task exists
        if not task:
            abort(404, message= "Task not found")
        # If category_id is being updated, check if the new category exists
        if task_data.get('category_id'):
            category = CategoryModel.query.get(task_data['category_id'])
            if not category:
                abort(400, message= "Bad Request")
        # 
        for key, value in task_data.items():
            setattr(task, key, value)
        task.updated_at = datetime.now()

        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            abort(400, message= "Failed to update task")


        task_schema = TaskSchema(many=False)
        serialized_task = task_schema.dump(task)
        return jsonify(serialized_task), 200

    # DELETE /tasks/:id: Deletes a task.
    def delete(self, task_id):
        """Delete a task."""
        # Check if task exists

        task = TaskModel.query.get(task_id)
        if not task:
            abort(404, message= "Task not found")

        try:
            db.session.delete(task)
            db.session.commit()
        except Exception:
            db.session.rollback()
            abort(400, message= "Failed to delete task")

        return {"message": "Task deleted"}, 200
