from flask_restful import reqparse
parser = reqparse.RequestParser()
parser.add_argument('link', required=True)
parser.add_argument('alias')
parser.add_argument('password')
