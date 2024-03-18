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
import validators

# import mutagen
cgitb.enable()

# Function to establish a connection with your MySQL database


def get_db_connection():
    conn = pymysql.connect(
                settings.DB_HOST,
                settings.DB_USER,
                settings.DB_PASSWD,
                settings.DB_DATABASE,
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor)
    return conn


def is_valid_url(url):
    return validators.url(url)


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

# Login


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
            return make_response(jsonify({'status': 'OK'}), 200)

        try:
            # Set up LDAP server connection
            ldapServer = Server(host=settings.LDAP_HOST)
            ldapConnection = Connection(ldapServer,
                                        raise_exceptions=True,
                                        user='uid=' +
                                        request_params['username'] +
                                        ', ou=People,ou=fcs,o=unb',
                                        password=request_params['password'])
            ldapConnection.open()
            ldapConnection.start_tls()
            ldapConnection.bind()  # LDAP authentication

            # Set up app database connection
            dbConnection = pymysql.connect(
                settings.DB_HOST,
                settings.DB_USER,
                settings.DB_PASSWD,
                settings.DB_DATABASE,
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor)

            # Check if the user exists in database by calling stored procedure getUser
            with dbConnection.cursor() as cursor:
                cursor.callproc(
                    'getUser', (request_params['username'],))
                result = cursor.fetchone()

            # If the user does not exist in the database
            if result is None:
                # Call the stored procedure add the user
                with dbConnection.cursor() as cursor:
                    cursor.callproc(
                        'addUser', (request_params['username']))
                    dbConnection.commit()
                # After the user is added, fetch the username
                with dbConnection.cursor() as cursor:
                    cursor.callproc('getUser',
                                    (request_params['username'],))
                    result = cursor.fetchone()
                username = result['username']
                response = {'status': 'Created', 'username': username}
                responseCode = 201
            else:
                username = result['username']
                response = {'status': 'OK', 'username': username}
                responseCode = 201

            # Set username in session
            session['username'] = username
        except LDAPException as e:
            if isinstance(e, LDAPOperationResult) and e.result == "invalidCredentials":
                response, responseCode = {
                    'status': 'Unauthorized', 'message': 'Invalid username or password'}, 401
            else:
                response, responseCode = {
                    'status': 'Internal Server Error', 'message': 'An LDAP error occurred'}, 500
        except MySQLError as e:
            response, responseCode = {'status': 'Internal Server Error',
                                      'message': 'Database not reachable or operation failed'}, 500
        finally:
            if 'ldapConnection' in locals() and ldapConnection.bound:
                ldapConnection.unbind()
            if dbConnection:
                dbConnection.close()

        return make_response(jsonify(response), responseCode)

# Logout


class Logout(Resource):
    # then logout where session gets deleted
    # Example
    # curl -i -H "Content-Type: application/json" -X DELETE -b cookie-jar http://cs3103.cs.unb.ca:8042/logout
    def delete(self):
        if 'username' in session:
            session.pop('username', None)
            response = {'status': 'success'}
            responseCode = 204
        else:
            response = {'status': 'fail'}
            responseCode = 403

        return make_response(jsonify(response), responseCode)


# Resource for retrieving user's links


class UserLinks(Resource):
    def get(self):
        if 'username' not in session:
            return make_response(jsonify({"error": "Authentication required"}), 403)

        username = session.get('username')

        try:
            # Establish database connection at the start within the try block
            conn = get_db_connection()

            links = []
            with conn.cursor() as cursor:
                cursor.callproc('getUserLinks', [username])
                links = cursor.fetchall()

            if not links:
                return make_response(jsonify({"error": "No links found for the user"}), 404)

            # Format the links for the response
            formatted_links = [
                {
                    "destination": link['destination'],
                    "short_url": f"{request.host_url}{link['shortcut']}"
                }
                for link in links
            ]

            return jsonify(formatted_links)
        except pymysql.MySQLError as e:
            return make_response(jsonify({"error": "Database error occurred"}), 500)
        finally:
            # Ensure the connection is closed in the finally block
            if 'conn' in locals():
                conn.close()



# Resource for link shortening


class CreateShortcut(Resource):
    def post(self):
        if 'username' not in session:
            return make_response(jsonify({"error": "Authentication required"}), 403)

        data = request.get_json()
        destination = data.get('destination')
        if not destination or not is_valid_url(destination):
            return make_response(jsonify({"error": "Invalid URL. Please try again with a valid URL."}), 400)

        username = session.get('username')
        # Establish database connection at the start
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.callproc('createLink', [destination, username])
                result = cursor.fetchone()
                conn.commit()

            if result:
                return make_response(jsonify({"short_url": f"{request.host_url}{result['generated_shortcut']}"}), 201)
            else:
                # If the stored procedure does not return a result, we assume link creation failed
                return make_response(jsonify({"error": "Failed to create link. Please try again later."}), 500)
        except pymysql.MySQLError as e:
            # Log the error or handle specific MySQL errors if needed
            return make_response(jsonify({"error": "Failed to create link due to a database error."}), 500)
        finally:
            conn.close()



# Resource for deleting a link


class DeleteLink(Resource):
    def delete(self, link_id):
        if 'username' not in session:
            return make_response(jsonify({"error": "Authentication required"}), 403)

        username = session.get('username')

        try:
            # Establish database connection at the start within the try block
            conn = get_db_connection()

            with conn.cursor() as cursor:
                # Check if the link exists and belongs to the user
                cursor.execute(
                    'SELECT * FROM links WHERE link_id = %s AND username = %s', (link_id, username))
                link = cursor.fetchone()

                if not link:
                    return make_response(jsonify({"error": "Link not found or access denied"}), 404)

                # Delete the link using the stored procedure
                cursor.callproc('deleteLink', [link_id])
                conn.commit()

            return ('', 204)
        except pymysql.MySQLError as e:
            return make_response(jsonify({"error": "Failed to delete link due to a database error."}), 500)
        finally:
            # Ensure the connection is closed in the finally block
            if 'conn' in locals():
                conn.close()




# Resource for getting link destination


class GetDestination(Resource):
    def get(self, shortcut):
        # Establish database connection at the start
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.callproc('getLinkDestination', [shortcut])
                result = cursor.fetchone()
                if result:
                    return redirect(result['destination'], code=302)  
                else:
                    return make_response(jsonify({"error": "Shortcut not found"}), 404)
        finally:
            conn.close()


# Register resources
api.add_resource(Login, '/users/login')
api.add_resource(Logout, '/users/logout')
api.add_resource(UserLinks, '/user/links')
api.add_resource(CreateShortcut, '/links')
api.add_resource(DeleteLink, '/link/<int:link_id>')
api.add_resource(GetDestination, '/links/shortcut/<string:shortcut>')

if __name__ == "__main__":
    context = ('cert.pem', 'key.pem')
    app.run(host=settings.APP_HOST,
            port=settings.APP_PORT,
            ssl_context=context,
            debug=settings.APP_DEBUG)
