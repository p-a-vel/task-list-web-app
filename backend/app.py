from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from datetime import datetime

app = Flask(__name__)
CORS(app)

# MongoDB Atlas URI
app.config["MONGO_URI"] = "mongodb+srv://dobriyaldevashish:Devashish%4023@cluster0.v8allzh.mongodb.net/todoapp?retryWrites=true&w=majority&appName=Cluster0"

try:
    mongo = PyMongo(app)
    mongo.db.list_collection_names()  # Test DB connection
    tasks = mongo.db.tasks
    print("✅ MongoDB connection successful!")
except Exception as e:
    print(f"❌ MongoDB connection failed: {e}")
    tasks = None


@app.route('/')
def home():
    return jsonify({
        "message": "Welcome to the Task Manager API!",
        "routes": {
            "GET /tasks": "List all tasks",
            "POST /tasks": "Create a new task",
            "GET /tasks/<id>": "Get a single task",
            "PUT /tasks/<id>": "Update a task",
            "DELETE /tasks/<id>": "Delete a task",
            "PATCH /tasks/<id>/status": "Update task status",
            "GET /tasks/stats": "Get task statistics",
            "GET /health": "Check health of the API"
        }
    })

# Get all tasks (with optional filtering)
@app.route('/tasks', methods=['GET'])
def get_tasks():
    if tasks is None:
        return jsonify({'error': 'Database connection failed'}), 500

    try:
        status = request.args.get('status')
        entity_name = request.args.get('entity_name')
        task_type = request.args.get('task_type')
        contact_person = request.args.get('contact_person')

        filter_query = {}
        if status:
            filter_query['status'] = status
        if entity_name:
            filter_query['entity_name'] = {'$regex': entity_name, '$options': 'i'}
        if task_type:
            filter_query['task_type'] = {'$regex': task_type, '$options': 'i'}
        if contact_person:
            filter_query['contact_person'] = {'$regex': contact_person, '$options': 'i'}

        output = []
        for task in tasks.find(filter_query).sort('creation_date', -1):
            output.append({
                'id': str(task['_id']),
                'creation_date': task['creation_date'].isoformat(),
                'entity_name': task['entity_name'],
                'task_type': task['task_type'],
                'task_time': task['task_time'].isoformat(),
                'date': task.get('date', ''),
                'contact_person': task['contact_person'],
                'phone_number': task.get('phone_number', ''),
                'note': task.get('note', ''),
                'status': task['status']
            })

        return jsonify(output)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Create a new task
@app.route('/tasks', methods=['POST'])
def add_task():
    if tasks is None:
        return jsonify({'error': 'Database connection failed'}), 500

    try:
        data = request.json
        required_fields = ['entity_name', 'task_type', 'task_time', 'contact_person', 'phone_number']
        for field in required_fields:
            if field not in data or not data[field].strip():
                return jsonify({'error': f'{field} is required'}), 400

        task_time = datetime.fromisoformat(data['task_time'].replace('Z', '+00:00'))
        new_task = {
            'creation_date': datetime.utcnow(),
            'entity_name': data['entity_name'].strip(),
            'task_type': data['task_type'].strip(),
            'task_time': task_time,
            'date': task_time.strftime('%d-%m-%Y'),
            'contact_person': data['contact_person'].strip(),
            'phone_number': data['phone_number'].strip(),
            'note': data.get('note', '').strip(),
            'status': data.get('status', 'open').strip().lower()
        }

        task_id = tasks.insert_one(new_task).inserted_id
        return jsonify({'id': str(task_id), 'message': 'Task created successfully'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Get a single task by ID
@app.route('/tasks/<id>', methods=['GET'])
def get_task(id):
    if tasks is None:
        return jsonify({'error': 'Database connection failed'}), 500

    try:
        task = tasks.find_one({'_id': ObjectId(id)})
        if not task:
            return jsonify({'error': 'Task not found'}), 404

        return jsonify({
            'id': str(task['_id']),
            'creation_date': task['creation_date'].isoformat(),
            'entity_name': task['entity_name'],
            'task_type': task['task_type'],
            'task_time': task['task_time'].isoformat(),
            'contact_person': task['contact_person'],
            'note': task.get('note', ''),
            'status': task['status']
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Update a task
@app.route('/tasks/<id>', methods=['PUT'])
def update_task(id):
    if tasks is None:
        return jsonify({'error': 'Database connection failed'}), 500

    try:
        data = request.json
        update_fields = {}

        if 'entity_name' in data:
            update_fields['entity_name'] = data['entity_name'].strip()
        if 'task_type' in data:
            update_fields['task_type'] = data['task_type'].strip()
        if 'task_time' in data:
            task_time = datetime.fromisoformat(data['task_time'].replace('Z', '+00:00'))
            update_fields['task_time'] = task_time
        if 'contact_person' in data:
            update_fields['contact_person'] = data['contact_person'].strip()
        if 'note' in data:
            update_fields['note'] = data['note'].strip()
        if 'status' in data:
            if data['status'] not in ['open', 'closed']:
                return jsonify({'error': 'Invalid status'}), 400
            update_fields['status'] = data['status']

        if not update_fields:
            return jsonify({'error': 'No valid fields to update'}), 400

        result = tasks.update_one({'_id': ObjectId(id)}, {'$set': update_fields})
        if result.modified_count:
            return jsonify({'message': 'Task updated successfully'})
        elif result.matched_count:
            return jsonify({'message': 'No changes made'})
        else:
            return jsonify({'error': 'Task not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Delete a task
@app.route('/tasks/<id>', methods=['DELETE'])
def delete_task(id):
    if tasks is None:
        return jsonify({'error': 'Database connection failed'}), 500

    try:
        result = tasks.delete_one({'_id': ObjectId(id)})
        if result.deleted_count:
            return jsonify({'message': 'Task deleted successfully'})
        return jsonify({'error': 'Task not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Update only the status
@app.route('/tasks/<id>/status', methods=['PATCH'])
def update_task_status(id):
    if tasks is None:
        return jsonify({'error': 'Database connection failed'}), 500

    try:
        data = request.json
        if 'status' not in data:
            return jsonify({'error': 'Status is required'}), 400
        if data['status'] not in ['open', 'closed']:
            return jsonify({'error': 'Invalid status'}), 400

        result = tasks.update_one({'_id': ObjectId(id)}, {'$set': {'status': data['status']}})
        if result.modified_count:
            return jsonify({'message': f'Status updated to {data["status"]}'})
        elif result.matched_count:
            return jsonify({'message': 'No changes made'})
        else:
            return jsonify({'error': 'Task not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Task stats
@app.route('/tasks/stats', methods=['GET'])
def get_task_stats():
    if tasks is None:
        return jsonify({'error': 'Database connection failed'}), 500

    try:
        total = tasks.count_documents({})
        open_count = tasks.count_documents({'status': 'open'})
        closed = tasks.count_documents({'status': 'closed'})

        task_types = list(tasks.aggregate([
            {'$group': {'_id': '$task_type', 'count': {'$sum': 1}}},
            {'$sort': {'count': -1}}
        ]))
        entities = list(tasks.aggregate([
            {'$group': {'_id': '$entity_name', 'count': {'$sum': 1}}},
            {'$sort': {'count': -1}}
        ]))

        return jsonify({
            'total_tasks': total,
            'open_tasks': open_count,
            'closed_tasks': closed,
            'task_types': [{'name': t['_id'], 'count': t['count']} for t in task_types],
            'entities': [{'name': e['_id'], 'count': e['count']} for e in entities]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Health check
@app.route('/health', methods=['GET'])
def health_check():
    try:
        if tasks is not None:
            mongo.db.list_collection_names()
            return jsonify({'status': 'healthy', 'database': 'connected'})
        else:
            return jsonify({'status': 'unhealthy', 'database': 'disconnected'}), 500
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 500

# Run the Flask app
if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
