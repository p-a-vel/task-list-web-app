from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from datetime import datetime
import pymongo

app = Flask(__name__)
CORS(app)

# Add your database name to the URI
app.config["MONGO_URI"] = "mongodb+srv://dobriyaldevashish:Devashish%4023@cluster0.v8allzh.mongodb.net/todoapp?retryWrites=true&w=majority&appName=Cluster0"

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)



try:
    mongo = PyMongo(app)
    # Test the connection
    mongo.db.list_collection_names()
    tasks = mongo.db.tasks
    print("MongoDB connection successful!")
except Exception as e:
    print(f"MongoDB connection failed: {e}")
    tasks = None

@app.route('/tasks', methods=['GET'])
def get_tasks():
    if tasks is None:
        return jsonify({'error': 'Database connection failed'}), 500

    try:
        # Get query parameters for filtering
        status = request.args.get('status')  # open/closed
        entity_name = request.args.get('entity_name')
        task_type = request.args.get('task_type')
        contact_person = request.args.get('contact_person')

        # Build filter query
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
        for task in tasks.find(filter_query).sort('creation_date', -1):  # Sort by newest first
            output.append({
                'id': str(task['_id']),
                'creation_date': task['creation_date'].isoformat() if isinstance(task['creation_date'], datetime) else task['creation_date'],
                'entity_name': task['entity_name'],
                'task_type': task['task_type'],
                'task_time': task['task_time'].isoformat() if isinstance(task['task_time'], datetime) else task['task_time'],
                'date': task.get('date', ''),  # added 'date' field (DD-MM-YYYY format)
                'contact_person': task['contact_person'],
                'phone_number': task.get('phone_number', ''),  # added phone_number
                'note': task.get('note', ''),
                'status': task['status']
            })

        return jsonify(output)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

    
from flask import request, jsonify
from datetime import datetime
from bson import ObjectId

@app.route('/tasks', methods=['POST'])
def add_task():
    if tasks is None:
        return jsonify({'error': 'Database connection failed'}), 500

    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        # Validate required fields
        required_fields = ['entity_name', 'task_type', 'task_time', 'contact_person', 'phone_number']
        for field in required_fields:
            if field not in data or (isinstance(data[field], str) and not data[field].strip()):
                return jsonify({'error': f'{field} is required'}), 400

        # Parse task_time if it's a string
        task_time = data['task_time']
        if isinstance(task_time, str):
            try:
                task_time = datetime.fromisoformat(task_time.replace('Z', '+00:00'))
            except ValueError:
                return jsonify({'error': 'Invalid task_time format. Use ISO format (YYYY-MM-DDTHH:MM:SS)'}), 400

        # Create new task document
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

        return jsonify({
            'id': str(task_id),
            'message': 'Task created successfully'
        }), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
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
            'creation_date': task['creation_date'].isoformat() if isinstance(task['creation_date'], datetime) else task['creation_date'],
            'entity_name': task['entity_name'],
            'task_type': task['task_type'],
            'task_time': task['task_time'].isoformat() if isinstance(task['task_time'], datetime) else task['task_time'],
            'contact_person': task['contact_person'],
            'note': task.get('note', ''),
            'status': task['status']
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/tasks/<id>', methods=['PUT'])
def update_task(id):
    if tasks is None:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Build update query
        update_fields = {}
        
        if 'entity_name' in data:
            update_fields['entity_name'] = data['entity_name'].strip()
        if 'task_type' in data:
            update_fields['task_type'] = data['task_type'].strip()
        if 'task_time' in data:
            task_time = data['task_time']
            if isinstance(task_time, str):
                try:
                    task_time = datetime.fromisoformat(task_time.replace('Z', '+00:00'))
                except ValueError:
                    return jsonify({'error': 'Invalid task_time format. Use ISO format (YYYY-MM-DDTHH:MM:SS)'}), 400
            update_fields['task_time'] = task_time
        if 'contact_person' in data:
            update_fields['contact_person'] = data['contact_person'].strip()
        if 'note' in data:
            update_fields['note'] = data['note'].strip()
        if 'status' in data:
            if data['status'] not in ['open', 'closed']:
                return jsonify({'error': 'Status must be either "open" or "closed"'}), 400
            update_fields['status'] = data['status']
        
        if not update_fields:
            return jsonify({'error': 'No valid fields to update'}), 400
        
        result = tasks.update_one(
            {'_id': ObjectId(id)},
            {'$set': update_fields}
        )
        
        if result.modified_count:
            return jsonify({'message': 'Task updated successfully'})
        elif result.matched_count:
            return jsonify({'message': 'No changes made'})
        else:
            return jsonify({'error': 'Task not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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

@app.route('/tasks/<id>/status', methods=['PATCH'])
def update_task_status(id):
    """Quick endpoint to update only the status of a task"""
    if tasks is None:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        data = request.json
        if not data or 'status' not in data:
            return jsonify({'error': 'Status is required'}), 400
        
        if data['status'] not in ['open', 'closed']:
            return jsonify({'error': 'Status must be either "open" or "closed"'}), 400
        
        result = tasks.update_one(
            {'_id': ObjectId(id)},
            {'$set': {'status': data['status']}}
        )
        
        if result.modified_count:
            return jsonify({'message': f'Task status updated to {data["status"]}'})
        elif result.matched_count:
            return jsonify({'message': 'Status unchanged'})
        else:
            return jsonify({'error': 'Task not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/tasks/stats', methods=['GET'])
def get_task_stats():
    """Get task statistics"""
    if tasks is None:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        total_tasks = tasks.count_documents({})
        open_tasks = tasks.count_documents({'status': 'open'})
        closed_tasks = tasks.count_documents({'status': 'closed'})
        
        # Get task types count
        task_types_pipeline = [
            {'$group': {'_id': '$task_type', 'count': {'$sum': 1}}},
            {'$sort': {'count': -1}}
        ]
        task_types = list(tasks.aggregate(task_types_pipeline))
        
        # Get entity names count
        entities_pipeline = [
            {'$group': {'_id': '$entity_name', 'count': {'$sum': 1}}},
            {'$sort': {'count': -1}}
        ]
        entities = list(tasks.aggregate(entities_pipeline))
        
        return jsonify({
            'total_tasks': total_tasks,
            'open_tasks': open_tasks,
            'closed_tasks': closed_tasks,
            'task_types': [{'name': item['_id'], 'count': item['count']} for item in task_types],
            'entities': [{'name': item['_id'], 'count': item['count']} for item in entities]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    try:
        if tasks is not None:
            # Test database connection
            mongo.db.list_collection_names()
            return jsonify({'status': 'healthy', 'database': 'connected'})
        else:
            return jsonify({'status': 'unhealthy', 'database': 'disconnected'}), 500
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 500

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)


