import os
from unicodedata import category
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10
def paginate_questons(request, selection):
    page = request.args.get('page', 1, type=int)
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE
    questions = [question.format() for question in selection]
    current_questions = questions[start:end]
    return current_questions

def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)
    CORS(app)

    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET, POST, PATCH, DELETE, OPTIONS')
        return response

    @app.route('/categories')
    def get_categories():
        categories = Category.query.all()
        current_categories = {category.id: category.type for category in categories}

        return jsonify({
            'success': True,
            'categories': current_categories     
        })

    @app.route('/questions')
    def get_questions():
        selection = Question.query.all()
        current_questions = paginate_questons(request, selection)

        if len(current_questions) == 0:
            abort(404)

        categories = Category.query.all()
        current_categories = {category.id: category.type for category in categories}

        return jsonify({
            'success': True,
            'questions': current_questions,
            'total_questions': len(current_questions),
            'categories': current_categories
        })

    @app.route('/questions/<int:question_id>', methods=['DELETE'])
    def delete_question(question_id):
        try:
            question = Question.query.filter(Question.id==question_id).one_or_none()
            if question is None:
                abort(404)

            question.delete()

            return jsonify({
                'success': True,
                'deleted': question_id,
                })
        except:
            abort(422)

    @app.route('/questions', methods=['POST'])
    def create_question():
        question = request.get_json()
        try:
            question = Question(
                question = question.get('question', None),
                answer = question.get('answer', None),
                category = question.get('category', None),
                difficulty = question.get('difficulty', None)
            )
            question.insert()

            selection = Question.query.order_by(Question.id).all()
            current_questions = paginate_questons(request, selection)

            return jsonify({
                'success': True,
                'created': question.id,
                'questions': current_questions,
                'total_questions': len(Question.query.all())
            })
        except:
            abort(422)

    @app.route('/questions/search', methods=['POST'])
    def search_questions():
        data = request.get_json()
        search = data.get('search_term')
        results = Question.query.filter(Question.question.ilike('%{}%'.format(search))).all()

        if results == []:
            abort(404)
            
        current_questions = paginate_questons(request, results)

        return jsonify({
            'success': True,
            'questions': current_questions,
            'total_questions': len(current_questions)
        })

    @app.route('/categories/<int:category_id>/questions')
    def get_questions_by_category(category_id):
        questions = Question.query.filter(Question.category==str(category_id)).all()
        current_questions = paginate_questons(request, questions)

        return jsonify({
            'success': True,
            'questions': current_questions,
            'total_questions': len(current_questions),
            'current_category': category_id
        })

    @app.route('/quizzes', methods=['POST'])
    def quiz():
        data = request.get_json()
        previous_questions = data.get('previous_questions')
        quiz_category = data.get('quiz_category')

        if quiz_category['id'] == 0:
            questions = Question.query.filter(
                Question.id.notin_(previous_questions)).all()
        else:
            questions = Question.query.filter(
                Question.id.notin_(previous_questions),
                Question.category == str(quiz_category['id'])).all()

        for question in questions:
            question = random.choice(questions)

        return jsonify({
            'success': True,
            'question': question.format()
        })

    
    # error handlers
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            "success": False,
            "error": 400,
            "message": "bad request"
        }), 400

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "success": False,
            "error": 404,
            "message": "page not found"
        }), 404

    @app.errorhandler(405)
    def invalid_method(error):
        return jsonify({
            "success": False,
            "error": 405,
            "message": "method not allowed"
        }), 405

    @app.errorhandler(422)
    def unprocessable_entity(error):
        return jsonify({
            "success": False,
            "error": 422,
            "message": "unprocessable entity"
        }), 422
    
    @app.errorhandler(500)
    def internal_server_error(error):
        return jsonify({
            "success": False,
            "error": 500,
            "message": "internal server error"
        }), 500

    return app

