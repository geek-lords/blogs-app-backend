from flask import Flask, request
from uuid import uuid4
from email_validator import validate_email, EmailNotValidError
import pymysql

from db_utilities import connection

error_code = 400
password_min = 6
password_max = 40
app = Flask(__name__)


@app.route("/create_account", methods=["POST"])
def create_account():
    try:
        if not request.json:
            print("JSON Data not found")
            return {"error": "JSON Data not found"}, error_code

        first_name = str(request.json['first_name']).strip()
        last_name = str(request.json['last_name']).strip()
        email = str(request.json['email']).strip()
        password = str(request.json['password']).strip()

        if len(first_name) == 0 or len(last_name) == 0 or len(email) == 0 or len(password) == 0:
            print("JSON Data can't be of length 0")
            return {"error": "JSON Data can't be of length 0"}, error_code

        try:
            email = validate_email(email).email
        except EmailNotValidError:
            print("Invalid Email Address")
            return {'error': "Invalid Email Address"}

        if len(password) < password_min or len(password) > password_max:
            print("Password Length should be between {0} to {1}".format(password_min, password_max))
            return {"error": "Password Length should be between {0} to {1}".format(password_min,
                                                                                   password_max)}, error_code

        with connection() as conn, conn.cursor(pymysql.cursors.DictCursor) as cur:
            user_id = str(uuid4())
            cur.execute("insert into Users(id, first_name, last_name, email_address, password) values(%s,%s,%s,%s,%s)",
                        (user_id, first_name, last_name, email, password))
            conn.commit()
            return {"user_id": user_id}, 200

    except KeyError:
        print("Important Data not found - Key Error")
        return {"error": "Important Data not found"}, error_code
    except pymysql.err.IntegrityError:
        print("User Information already exists")
        return {"error": "User Information already exists"}, error_code


@app.route("/authenticate", methods=["POST"])
def authenticate_user():
    try:
        if not request.json:
            print("JSON Data not found")
            return {"error": "JSON Data not found"}
        email = str(request.json['email']).strip()
        password = str(request.json['password']).strip()
        with connection() as conn, conn.cursor(pymysql.cursors.DictCursor) as cur:
            cur.execute("Select id, password from Users where email_address = %s ", email)
            if cur.rowcount == 0:
                print("Invalid Email or Password")
                return {"error": "Invalid Email or Password"}, error_code
            row = cur.fetchone()
            if password != row['password']:
                print("Email and Password doens't match")
                return {"error": "Email and Password doesn't match."}, error_code
        return {"user_id": str(row['id'])}
    except KeyError:
        print("Important Data not found - Key Error")
        return {"error": "Important Data not found"}, error_code


if __name__ == "__main__":
    app.run(debug=True)
