from flask import jsonify


def success_response(data=None, message=None, status_code=200):
    body = {'success': True}
    if data is not None:
        body['data'] = data
    if message:
        body['message'] = message
    return jsonify(body), status_code


def created_response(data=None, message=None):
    return success_response(data=data, message=message, status_code=201)


def no_content_response():
    return '', 204


def error_response(error_code, message, status_code=400):
    return jsonify({
        'success': False,
        'error': error_code,
        'message': message,
    }), status_code


def paginated_response(items, page, per_page, total):
    import math
    return jsonify({
        'success': True,
        'data': items,
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': total,
            'pages': math.ceil(total / per_page) if per_page else 1,
        },
    }), 200


def validation_error_response(errors):
    return jsonify({
        'success': False,
        'error': 'VALIDATION_ERROR',
        'message': 'Validation failed',
        'errors': errors,
    }), 422
