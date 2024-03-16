#!/usr/bin/env python3
# activate_this = '/var/www/html/hhong/myenv/bin/activate_this.py'
# exec(open(activate_this).read(), {'__file__': activate_this})

import settings  # Our server and db settings, stored in settings.py
from flask import Flask, jsonify, abort, request, make_response, session
from flask_restful import reqparse, Resource, Api
from flask_session import Session
import pymysql.cursors
import json
import os
import ssl
from ldap3 import Server, Connection, ALL
from ldap3.core.exceptions import *
import cgitb
import cgi
import sys
import datetime
# import mutagen
cgitb.enable()

# Function to establish a connection with your MySQL database
def get_db_connection():
    conn = pymysql.connect(host=settings.DB_HOST,
                           user=settings.DB_USER,
                           password=settings.DB_PASS,
                           db=settings.DB_NAME,
                           cursorclass=pymysql.cursors.DictCursor)
    return conn


app = Flask(__name__, static_url_path='/static')
# Set Server-side session config: Save sessions in the local app directory.
app.secret_key = settings.SECRET_KEY
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_COOKIE_NAME'] = 'peanutButter'
app.config['SESSION_COOKIE_DOMAIN'] = settings.APP_HOST
Session(app)

# Running api service
api = Api(app)


####################################################################################
#
# Error handlers
#
@app.errorhandler(400)  # decorators to add to 400 response
def not_found(error):
    return make_response(jsonify({"status": "Bad request"}), 400)


@app.errorhandler(404)  # decorators to add to 404 response
def not_found(error):
    return make_response(jsonify({"status": "Resource not found"}), 404)

####################################################################################
#
# Static Endpoints for humans
#


class Root(Resource):
    # get method. What might others be aptly named? (hint: post)
    def get(self):
        return app.send_static_file('index.html')


api.add_resource(Root, '/')


class Developer(Resource):
   # get method. What might others be aptly named? (hint: post)
    def get(self):
        return app.send_static_file('developer.html')


api.add_resource(Developer, '/dev')

# Control Login/ Logout Session
# Handles Cookie


class Login(Resource):
    #
    # Set Session and return Cookie
    #
    # Example curl command:
    # curl -i -H "Content-Type: application/json" -X POST -d '{"username": "hhong", "password": "your unb password"}' -c cookie-jar -k http://cs3103.cs.unb.ca:8042/login
    #
    def post(self):
        if not request.json:
            abort(400)  # bad request

        # Parse the JSON
        parser = reqparse.RequestParser()
        try:
            # Required attributes in the JSON document
            parser.add_argument('username', type=str, required=True)
            parser.add_argument('password', type=str, required=True)
            request_params = parser.parse_args()
        except:
            abort(400)  # bad request

        # If the user is already logged in
        if 'username' in session and session['username'] == request_params['username']:
            return jsonify({'status': 'Already logged in'})

        try:
            # LDAP server call for authentication
            ldapServer = Server(host=settings.LDAP_HOST, use_ssl=True)
            ldapConnection = Connection(ldapServer,
                                        user=f'uid={
                                            request_params["username"]},ou=People,ou=fcs,o=unb',
                                        password=request_params['password'])
            if not ldapConnection.bind():
                return jsonify({'status': 'LDAP authentication failed'}), 401

            # Check if user exists in local database and/or add them
            conn = get_db_connection()
            with conn.cursor() as cursor:
                cursor.callproc('addUser', [request_params['user_id']])
                conn.commit()  # Commit to save any changes

                # Fetch the user_id of the authenticated user
                cursor.execute(
                    'SELECT user_id FROM users WHERE username = %s', (request_params['username'],))
                user_id = cursor.fetchone()['user_id']

            # Store username and user_id in the session
            session['username'] = request_params['username']
            session['user_id'] = user_id

            return jsonify({'status': 'success', 'session_id': session.sid}), 201
        except Exception as e:
            return jsonify({'status': 'Error', 'message': str(e)}), 500
        finally:
            if ldapConnection:
                ldapConnection.unbind()

    # GET: Check Cookie data with Session data
    #
    # Example curl command:
    # curl -i -H "Content-Type: application/json" -X GET -b cookie-jar http://cs3103.cs.unb.ca:8042/login
    def get(self):
        if 'user_id' in session:
            user_id = session['user_id']
            response = {'status': 'success'}
            responseCode = 200
        else:
            response = {'status': 'fail'}
            responseCode = 403

        return make_response(jsonify(response), responseCode)


class Logout(Resource):
    # then logout where session gets deleted
    # Example
    # curl -i -H "Content-Type: application/json" -X DELETE -b cookie-jar http://cs3103.cs.unb.ca:8042/logout
    def delete(self):
        if 'user_id' in session:
            session.pop('user_id', None)
            response = {'status': 'success'}
            responseCode = 200
        else:
            response = {'status': 'fail'}
            responseCode = 403

        return make_response(jsonify(response), responseCode)


# Resource for retrieving user's links


class UserLinks(Resource):
    def get(self):
        if 'user_id' not in session:
            return make_response(jsonify({"error": "Authentication required"}), 403)

        user_id = session.get('user_id')

        conn = get_db_connection()
        links = []
        with conn.cursor() as cursor:
            cursor.callproc('getUserLinks', [user_id])
            for link in cursor.fetchall():
                links.append({
                    "destination": link['destination'],
                    "short_url": f"{request.host_url}{link['shortcut']}"
                })

        return jsonify(links)

# Resource for link shortening


class CreateShortcut(Resource):
    def post(self):
        if 'user_id' not in session:
            return make_response(jsonify({"error": "Authentication required"}), 403)

        data = request.get_json()
        destination = data.get('destination')
        if not destination:
            return make_response(jsonify({"error": "Missing destination URL"}), 400)

        user_id = session.get('user_id')

        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.callproc('createLink', [destination, user_id])
            result = cursor.fetchone()
            conn.commit()

        if result:
            return make_response(jsonify({"short_url": f"{request.host_url}{result['generated_shortcut']}"}), 201)
        else:
            return make_response(jsonify({"error": "Failed to create link"}), 500)


# Resource for deleting a link


class DeleteLink(Resource):
    def delete(self, link_id):
        if 'username' not in session:
            return make_response(jsonify({"error": "Authentication required"}), 403)

        user_id = session.get('user_id')

        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                'DELETE FROM links WHERE link_id = %s AND user_id = %s', (link_id, user_id))
            if cursor.rowcount == 0:
                return make_response(jsonify({"error": "Link not found or access denied"}), 404)
            conn.commit()

        return make_response(jsonify({"success": "Link deleted"}), 200)

# Resource for getting link destination


class GetDestination(Resource):
    def get(self, shortcut):
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.callproc('getLinkDestination', [shortcut])
            result = cursor.fetchone()
            if result:
                return redirect(result['destination'], code=302)
            else:
                return jsonify({"error": "Shortcut not found"}), 404


# Register resources
api.add_resource(Login, '/users/login')
api.add_resource(Logout, '/users/logout')
api.add_resource(UserLinks, '/user/links')
api.add_resource(CreateShortcut, '/links')
api.add_resource(DeleteLink, '/link/<int:link_id>')
api.add_resource(GetDestination, '/links/shortcut/<string:shortcut>')

if __name__ == "__main__":
    app.run(host=settings.APP_HOST, port=settings.APP_PORT,
            debug=settings.APP_DEBUG)
