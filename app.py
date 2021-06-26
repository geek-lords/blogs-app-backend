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


@app.route("/create_blog", methods=["POST"])
def create_blog():
    if not request.json:
        return {"error", "JSON Data not found"}, error_code
    try:
        user_id = str(request.json["user_id"]).strip()
        title = str(request.json["title"]).strip()
        content = str(request.json["content"]).strip()

        with connection() as conn, conn.cursor(pymysql.cursors.DictCursor) as cur:
            cur.execute("select id from Users where id = %s ", user_id)
            if cur.rowcount == 0:
                return {"error": "User doesn't exists."}, error_code
            blog_id = str(uuid4())
            cur.execute("insert into blog(id, user_id, title, content) values(%s, %s, %s, %s)",
                        (blog_id, user_id, title, content))
            conn.commit()
            return {"blog_id": blog_id}
    except KeyError:
        print("Important Data not found - Key Error")
        return {"error": "Important Data not found"}, error_code
    except pymysql.err.IntegrityError:
        print("User Information already exists")
        return {"error": "User Information already exists"}, error_code


@app.route("/fetch_blogs", methods=["GET"])
def fetch_blogs():
    try:
        if not request.json:
            return {"error": "JSON Data not found"}

        user_id = str(request.json['user_id']).strip()

        with connection() as conn, conn.cursor(pymysql.cursors.DictCursor) as cur:
            cur.execute("Select id from Users where id = %s", user_id)
            if cur.rowcount == 0:
                return {"error": "Invalid User."}, error_code
            cur.execute(
                "select blog.id, blog.title, blog.content, blog.like_count, "
                "Users.first_name, Users.last_name, Users.email_address "
                "from blog join Users "
                "on blog.user_id = Users.id "
                "where blog.user_id <> %s",
                user_id)
            return {"list_blogs": cur.fetchall()}, 200
    except KeyError:
        print("Important Data not found - Key Error")
        return {"error": "Important Data not found"}, error_code


@app.route("/fetch_blogs/<blog_id>", methods=["GET"])
def fetch_blog(blog_id):
    if not request.json:
        return {"error": "JSON Data not found"}
    try:
        user_id = str(request.json['user_id']).strip()
        with connection() as conn, conn.cursor(pymysql.cursors.DictCursor) as cur:
            cur.execute("select id from Users where id = %s", user_id)
            if cur.rowcount == 0:
                return {"error": "Invalid user"}, error_code
            cur.execute("select blog.id, blog.title, blog.content, blog.like_count, "
                        "Users.first_name, Users.last_name, Users.email_address "
                        "from blog join Users "
                        "on blog.user_id = Users.id where blog.id = %s", blog_id)
            blog = cur.fetchone()
            cur.execute("select Users.first_name, Users.last_name, comments.comment from Users join comments on Users.id = comments.user_id where comments.blog_id = %s",blog_id)
            comments = cur.fetchall()
            return {"blog": blog, "comments": comments}
    except KeyError:
        print("Important Data not found - Key Error")
        return {"error": "Important Data not found"}, error_code


@app.route("/like/<blog_id>", methods=["POST"])
def like(blog_id):
    if not request.json:
        return {"error": "User must be Logged In to like a Blog."}, error_code
    try:
        user_id = str(request.json["user_id"]).strip()
        ld = str(request.json["like_dislike"]).strip()
        with connection() as conn, conn.cursor(pymysql.cursors.DictCursor) as cur:
            cur.execute("select id from Users where id = %s", user_id)
            if cur.rowcount == 0:
                return {"error": "Invalid User"}, error_code
            cur.execute("Select user_id, like_count from blog where id = %s", blog_id)
            row = cur.fetchone()
            if row['user_id'] == user_id:
                return {"error": "You can't like your own blogs."}, error_code
            new_like = int(row['like_count']) + int(ld)
            cur.execute("update blog set like_count = %s where id = %s ", (new_like, blog_id))
            conn.commit()
        return {"success": "Blog liked Successfully."}, 200
    except KeyError:
        print("Important Data not found - Key Error")
        return {"error": "Important Data not found"}, error_code


@app.route("/comment/<blog_id>", methods=["POST"])
def comment(blog_id):
    try:
        if not request.json:
            return {"error": "JSON Data not found"}, error_code
        user_id = str(request.json['user_id']).strip()
        comment = str(request.json['comment']).strip()
        with connection() as conn, conn.cursor(pymysql.cursors.DictCursor) as cur:
            cur.execute("select id from Users where id = %s", user_id)
            if cur.rowcount == 0:
                return {"error": "Invalid User"}, error_code
            cur.execute("insert into comments(blog_id, user_id, comment) values(%s,%s,%s) ",
                        (blog_id, user_id, comment))
            conn.commit()
            return {"success": "Comment Successfully added"}, 200
    except KeyError:
        print("Important Data not found - Key Error")
        return {"error": "Important Data not found"}, error_code


if __name__ == "__main__":
    app.run(debug=True)
