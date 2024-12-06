import secrets
import string

from flask import jsonify, request
from flask_restful import Resource, abort
from data.reqpase_link import parser
from data import db_session
from data.users import User
from data.links import Link
from data.transitions import Transition


def generate_alphanum_crypt_string(length):
    letters_and_digits = string.ascii_letters + string.digits
    crypt_rand_string = ''.join(secrets.choice(
        letters_and_digits) for i in range(length))
    return crypt_rand_string


def abort_if_news_not_found(links_alias, user):
    session = db_session.create_session()
    link = session.query(Link).filter(Link.user == user, Link.alias == links_alias).first()
    if not link:
        abort(404, message=f"Link {links_alias} not found")


class LinksResource(Resource):
    def get(self, links_alias):
        api_token = request.headers.get('api_token')
        if api_token:
            session = db_session.create_session()
            user = session.query(User).filter(User.apikey == api_token).first()
            if user:
                abort_if_news_not_found(links_alias, user)
                link = session.query(Link).filter(Link.user == user, Link.alias == links_alias).first()
                transitions = len(session.query(Transition).filter(Transition.link_id == link.id).all())
                _link = link.to_dict(only=('link', 'alias', 'created_date'))
                _link.update({'transitions': transitions})
                return jsonify({'link': _link})
            return jsonify({'errors': "Invalid api_token"})
        else:
            return jsonify({'errors': "Not api_token"})

    def delete(self, links_alias):
        api_token = request.headers.get('api_token')
        if api_token:
            session = db_session.create_session()
            user = session.query(User).filter(User.apikey == api_token).first()
            if user:
                abort_if_news_not_found(links_alias, user)
                link = session.query(Link).filter(Link.user == user, Link.alias == links_alias).first()
                session.delete(link)
                session.commit()
                return jsonify({'success': 'OK'})
            return jsonify({'errors': "Invalid api_token"})
        else:
            return jsonify({'errors': "Not api_token"})


class LinksListResource(Resource):
    def get(self):
        api_token = request.headers.get('api_token')
        if api_token:
            session = db_session.create_session()
            user = session.query(User).filter(User.apikey == api_token).first()
            if user:
                links = session.query(Link).filter(Link.user == user).all()
                return jsonify({'links': [item.to_dict(
                    only=('link', 'alias', 'created_date')) for item in links]})
            return jsonify({'errors': "Invalid api_token"})
        else:
            return jsonify({'errors': "Not api_token"})

    def post(self):
        api_token = request.headers.get('api_token')
        if api_token:
            session = db_session.create_session()
            user = session.query(User).filter(User.apikey == api_token).first()
            if user:
                args = parser.parse_args()
                if not session.query(Link).filter(Link.alias == args['alias']).first():
                    link = Link()
                    link.set_link(args['link'])
                    if not args['alias']:
                        link.alias = generate_alphanum_crypt_string(5)
                    else:
                        link.alias = args['alias']
                    if args['password']:
                        link.set_password(args['password'])
                    link.user_id = user.id
                    session.add(link)
                    session.commit()
                    return jsonify({'success': 'OK'})
                else:
                    return jsonify({'errors': "Alias is busy "})
            return jsonify({'errors': "Invalid api_token"})
        else:
            return jsonify({'errors': "Not api_token"})
