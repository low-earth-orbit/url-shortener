#!/usr/bin/env python3
# activate_this = '/var/www/html/hhong/myenv/bin/activate_this.py'
# exec(open(activate_this).read(), {'__file__': activate_this})

import settings  # Our server and db settings, stored in settings.py
from flask import Flask, jsonify, abort, request, make_response, session, redirect
from flask_restful import reqparse, Resource, Api
from flask_session import Session
from flask_cors import CORS
import pymysql.cursors
from pymysql import MySQLError
from ldap3 import Server, Connection, ALL
from ldap3.core.exceptions import *
import cgitb
import validators

# import mutagen
cgitb.enable()

# Function to establish a connection with your MySQL database


def get_db_connection():
    conn = pymysql.connect(
        host=settings.DB_HOST,
        user=settings.DB_USER,
        password=settings.DB_PASSWD,
        database=settings.DB_DATABASE,
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor)
    return conn


def is_valid_url(url):
    return validators.url(url)


app = Flask(__name__, static_url_path='/')

CORS(app, supports_credentials=True)  # For local development only

# Set Server-side session config: Save sessions in the local app directory.
app.secret_key = settings.SECRET_KEY
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_COOKIE_NAME'] = 'peanutButter'
app.config['SESSION_COOKIE_DOMAIN'] = settings.APP_HOST
app.config['SESSION_COOKIE_SECURE'] = True  # For local development only
app.config['SESSION_COOKIE_SAMESITE'] = 'None'  # For local development only

# Initialize Session
Session(app)

# Running api service
api = Api(app)

# Error handlers


@app.errorhandler(400)  # decorators to add to 400 response
def not_found(error):
    return make_response(jsonify({"status": "Bad request"}), 400)


@app.errorhandler(404)  # decorators to add to 404 response
def not_found(error):
    return make_response(jsonify({"status": "Resource not found"}), 404)

@app.route('/check-session', methods=['GET'])
def check_session():
    if 'username' in session:
        return jsonify({'isLoggedIn': True, 'username': session['username']})
    else:
        return jsonify({'isLoggedIn': False})

# App root


class Root(Resource):
    def get(self):
        return app.send_static_file('index.html')


api.add_resource(Root, '/')


class Api(Resource):
    def get(self):
        return app.send_static_file('api.html')


api.add_resource(Api, '/api')

# Login


class Login(Resource):
    # Example curl command:
    # curl -i -H "Content-Type: application/json" -X POST -d '{"username": "<username>", "password": "<password>"}' -b cookie-jar -c cookie-jar -k https://cs3103.cs.unb.ca:8042/login
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
            return make_response(jsonify({'status': 'Already logged in'}), 200)

        dbConnection = None
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
            dbConnection = get_db_connection()

            # Check if the user exists in database by calling stored procedure getUser
            with dbConnection.cursor() as cursor:
                cursor.callproc('getUser', (request_params['username'],))
                result = cursor.fetchone()

            # If the user does not exist in the database
            if result is None:
                # Call the stored procedure add the user
                with dbConnection.cursor() as cursor:
                    cursor.callproc('addUser', (request_params['username'],))
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
                responseCode = 200

            # Set username in session
            session['username'] = username
        except LDAPException:
            response, responseCode = {
                'status': 'Unauthorized', 'message': 'Invalid username or password'}, 401
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
    # Example curl command:
    # curl -i -H "Content-Type: application/json" -X DELETE -b cookie-jar -k https://cs3103.cs.unb.ca:8042/logout
    def delete(self):
        session.pop('username', None)

        response = make_response('', 204)
        response.set_cookie('sessionId', '', expires=0,
                            httponly=True, secure=True, path='/')

        return response


# Resource for managing user's links


class UserLinks(Resource):
    # Example curl command:
    # curl -i -H "Content-Type: application/json" -X GET -b cookie-jar -k https://cs3103.cs.unb.ca:8042/user/links
    def get(self):
        if 'username' not in session:
            return make_response(jsonify({"error": "Authentication required"}), 401)

        username = session.get('username')

        conn = None
        try:
            conn = get_db_connection()

            links = []
            with conn.cursor() as cursor:
                cursor.callproc('getUserLinks', [username])
                links = cursor.fetchall()

            # Format the links for the response
            formatted_links = [
                {
                    "linkId": link['link_id'],
                    "destination": link['destination'],
                    "shortcut": link['shortcut'],
                    "username": link['username']
                }
                for link in links
            ]

            return make_response(jsonify(formatted_links), 200)
        except MySQLError as e:
            return make_response(jsonify({"error": "Database error occurred"}), 500)
        finally:
            if 'conn' in locals():
                conn.close()

    # Example curl command:
    # curl -i -H "Content-Type: application/json" -X POST -d '{"destination": "<full_url>"}' -b cookie-jar -k https://cs3103.cs.unb.ca:8042/user/links
    def post(self):
        if 'username' not in session:
            return make_response(jsonify({"error": "Authentication required"}), 401)

        data = request.get_json()
        destination = data.get('destination')
        if not destination or not is_valid_url(destination):
            return make_response(jsonify({"error": "Invalid URL. Please try again with a valid URL."}), 400)

        username = session.get('username')

        conn = None
        try:
            conn = get_db_connection()

            with conn.cursor() as cursor:
                cursor.callproc('createLink', [destination, username])
                result = cursor.fetchone()
                conn.commit()

            # Format the link for the response
            link = {
                "linkId": result['link_id'],
                "destination": result['destination'],
                "shortcut": result['shortcut'],
                "username": result['username']
            }

            if result:
                return make_response(jsonify(link), 201)
            else:
                return make_response(jsonify({"error": "Failed to create link. Please try again later."}), 500)
        except MySQLError as e:
            return make_response(jsonify({"error": "Failed to create link due to a database error."}), 500)
        finally:
            if 'conn' in locals():
                conn.close()


# Resource for deleting a link


class DeleteLink(Resource):
    # Example curl command:
    # curl -i -H "Content-Type: application/json" -X DELETE -b cookie-jar -k https://cs3103.cs.unb.ca:8042/user/links/<link_id>
    def delete(self, link_id):
        if 'username' not in session:
            return make_response(jsonify({"error": "Authentication required"}), 401)

        username = session.get('username')

        conn = None
        try:
            conn = get_db_connection()

            with conn.cursor() as cursor:
                # Get the link that belongs to the user
                cursor.callproc('getUserLink', [link_id, username])
                link = cursor.fetchone()

                if not link:
                    return make_response(jsonify({"error": "Link not found for the user"}), 404)

                # Delete the link using the stored procedure
                cursor.callproc('deleteLink', (link['link_id'],))
                conn.commit()

            return make_response('', 204)
        except MySQLError as e:
            return make_response(jsonify({"error": "Failed to delete link due to a database error."}), 500)
        finally:
            if 'conn' in locals():
                conn.close()


# Resource for getting link destination


class GetDestination(Resource):
    # Example curl command:
    # curl -i -H "Content-Type: application/json" -X GET -k https://cs3103.cs.unb.ca:8042/<shortcut>
    def get(self, shortcut):
        conn = None
        try:
            conn = get_db_connection()

            with conn.cursor() as cursor:
                cursor.callproc('getLinkDestination', [shortcut])
                result = cursor.fetchone()

            if result:
                return redirect(result['destination'], code=302)
            else:
                return make_response(jsonify({"error": "Shortcut not found"}), 404)
        except MySQLError as e:
            return make_response(jsonify({"error": "Database error occurred"}), 500)
        finally:
            if 'conn' in locals():
                conn.close()


# Register resources
api.add_resource(Login, '/login')
api.add_resource(Logout, '/logout')
api.add_resource(UserLinks, '/user/links')
api.add_resource(DeleteLink, '/user/links/<int:link_id>')
api.add_resource(GetDestination, '/<string:shortcut>')

if __name__ == "__main__":
    context = ('cert.pem', 'key.pem')
    app.run(host=settings.APP_HOST,
            port=settings.APP_PORT,
            ssl_context=context,
            debug=settings.APP_DEBUG)
