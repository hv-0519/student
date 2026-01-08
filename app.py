from flask import Flask, request, redirect, render_template, url_for
import sqlite3
import random
import string
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# ---------------- Helper Functions ----------------
def send_email(
    to_email,
    subject,
    body,
    from_email="jay451428@gmail.com",
    from_password="xpya nqal apnd jxqe",  # Use environment variables in production!
):
    msg = MIMEMultipart()
    msg["From"] = from_email
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(from_email, from_password)
        server.send_message(msg)
        server.quit()
    except Exception as e:
        print("Email sending failed:", e)  # Log in production


def generate_username(fname, lname):
    return f"{fname.lower()}.{lname.lower()}{random.randint(100, 999)}"


def generate_password(length=8):
    return "".join(random.choices(string.ascii_letters + string.digits, k=length))


def user_exists(username, role=None):
    conn = sqlite3.connect("database/exam.db")
    cursor = conn.cursor()
    if role:
        cursor.execute(
            "SELECT 1 FROM users WHERE username=? AND role=?", (username, role)
        )
    else:
        cursor.execute("SELECT 1 FROM users WHERE username=?", (username,))
    res = cursor.fetchone()
    conn.close()
    return bool(res)


def get_admin_data(username, table_name, single=False, where_clause=None, params=()):
    # Admin validation
    if not username or not user_exists(username, "admin"):
        return None, redirect(url_for("login"))

    conn = sqlite3.connect("database/exam.db")
    cursor = conn.cursor()

    query = f"SELECT * FROM {table_name}"
    if where_clause:
        query += f" WHERE {where_clause}"

    cursor.execute(query, params)

    if single:
        data = cursor.fetchone()
    else:
        data = cursor.fetchall()

    conn.close()
    return data, None


# ---------------- Public Routes ----------------
@app.route("/")
def hello():
    return render_template("common/index.html")


@app.route("/features")
def features():
    return render_template("common/features.html")


@app.route("/about")
def about_us():
    return render_template("common/about_us.html")


# ---------------- Register ----------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        fname = request.form["fname"]
        lname = request.form["lname"]
        email = request.form.get("email")

        username = generate_username(fname, lname)
        raw_password = generate_password()
        password_hash = generate_password_hash(raw_password)

        conn = sqlite3.connect("database/exam.db")
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO users (username, password_hash, role, is_temp_password) VALUES (?, ?, ?, 1)",
            (username, password_hash, "student"),
        )
        user_id = cursor.lastrowid

        cursor.execute(
            "INSERT INTO student_profiles (user_id, first_name, last_name, email) VALUES (?, ?, ?, ?)",
            (user_id, fname, lname, email),
        )

        conn.commit()
        conn.close()

        if email:
            send_email(
                to_email=email,
                subject="Your ExamPro Account Credentials",
                body=f"""Hello {fname},

Welcome to ExamPro!

Your account has been created.

Username: {username}
Temporary Password: {raw_password}

Please log in and change your password immediately.

Thank you!
""",
            )

        return redirect(url_for("login"))

    return render_template("common/register.html")


# ---------------- Login ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect("database/exam.db")
        cursor = conn.cursor()
        cursor.execute(
            "SELECT password_hash, role, is_temp_password FROM users WHERE username=?",
            (username,),
        )
        user = cursor.fetchone()
        conn.close()

        if not user or not check_password_hash(user[0], password):
            return render_template(
                "common/login.html", error="Invalid username or password"
            )

        role, is_temp_password = user[1], user[2]

        if role == "student" and is_temp_password:
            return redirect(url_for("update_password", username=username))

        if role == "admin":
            return redirect(url_for("admin_dashboard", username=username))

        return redirect(url_for("student_dashboard", username=username))

    return render_template("common/login.html")


# ---------------- Update Password (Forced or Voluntary) ----------------
@app.route("/update_password", methods=["GET", "POST"])
def update_password():
    username = request.args.get("username") or request.form.get("username")

    if not username:
        return redirect(url_for("login"))

    if request.method == "POST":
        old_password = request.form["old_password"]
        new_password = request.form["new_password"]
        confirm_password = request.form["confirm_password"]

        if new_password != confirm_password:
            return render_template(
                "common/update_password.html",
                username=username,
                error="Passwords do not match!",
            )

        conn = sqlite3.connect("database/exam.db")
        cursor = conn.cursor()
        cursor.execute(
            "SELECT password_hash, is_temp_password FROM users WHERE username=?",
            (username,),
        )
        user = cursor.fetchone()

        if not user or not check_password_hash(user[0], old_password):
            conn.close()
            return render_template(
                "common/update_password.html",
                username=username,
                error="Old password is incorrect!",
            )

        new_hash = generate_password_hash(new_password)

        cursor.execute(
            "UPDATE users SET password_hash=?, is_temp_password=0 WHERE username=?",
            (new_hash, username),
        )
        conn.commit()
        conn.close()

        return redirect(url_for("login"))

    return render_template("common/update_password.html", username=username)


# ---------------- Forgot Password Flow ----------------
@app.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form["email"]

        conn = sqlite3.connect("database/exam.db")
        cursor = conn.cursor()
        cursor.execute(
            """SELECT u.user_id, u.username 
               FROM users u 
               JOIN student_profiles sp ON u.user_id = sp.user_id 
               WHERE sp.email = ?""",
            (email,),
        )
        res = cursor.fetchone()

        if not res:
            conn.close()
            return render_template(
                "common/forgot_password.html", error="Email not found!"
            )

        user_id, username = res

        reset_code = "".join(random.choices(string.ascii_letters + string.digits, k=6))

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS password_resets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                reset_code TEXT,
                is_used INTEGER DEFAULT 0
            )
        """
        )

        cursor.execute(
            "INSERT INTO password_resets (user_id, reset_code) VALUES (?, ?)",
            (user_id, reset_code),
        )
        conn.commit()
        conn.close()

        send_email(
            to_email=email,
            subject="ExamPro Password Reset Code",
            body=f"""Hello {username},

Your password reset code is: {reset_code}

Enter this code on the verification page to set a new password.

This code is valid for one use only.
""",
        )

        return redirect(url_for("verify_code"))

    return render_template("common/forgot_password.html")


@app.route("/verify_code", methods=["GET", "POST"])
def verify_code():
    if request.method == "POST":
        entered_code = request.form["reset_code"]

        conn = sqlite3.connect("database/exam.db")
        cursor = conn.cursor()
        cursor.execute(
            "SELECT user_id FROM password_resets WHERE reset_code = ? AND is_used = 0",
            (entered_code,),
        )
        res = cursor.fetchone()

        if not res:
            conn.close()
            return render_template(
                "common/verify_code.html", error="Invalid or expired code!"
            )

        user_id = res[0]
        cursor.execute(
            "UPDATE password_resets SET is_used = 1 WHERE reset_code = ?",
            (entered_code,),
        )
        conn.commit()
        conn.close()

        return redirect(url_for("reset_password", user_id=user_id))

    return render_template("common/verify_code.html")


@app.route("/reset_password", methods=["GET", "POST"])
def reset_password():
    user_id = request.args.get("user_id")
    if not user_id:
        return redirect(url_for("forgot_password"))

    if request.method == "POST":
        new_password = request.form["new_password"]
        confirm_password = request.form["confirm_password"]

        if new_password != confirm_password:
            return render_template(
                "common/reset_password.html",
                user_id=user_id,
                error="Passwords do not match!",
            )

        hashed = generate_password_hash(new_password)

        conn = sqlite3.connect("database/exam.db")
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET password_hash = ?, is_temp_password = 0 WHERE user_id = ?",
            (hashed, user_id),
        )
        cursor.execute(
            "UPDATE password_resets SET is_used = 1 WHERE user_id = ?", (user_id,)
        )
        conn.commit()
        conn.close()

        return redirect(url_for("login"))

    return render_template("common/reset_password.html", user_id=user_id)


# ---------------- Admin Routes ----------------#
# ---------------- Dashboards ----------------
@app.route("/admin/dashboard")
def admin_dashboard():
    username = request.args.get("username")
    # dashboard has no table data
    if not username or not user_exists(username, "admin"):
        return redirect(url_for("login"))
    return render_template("admin/admin_dashboard.html", username=username)


@app.route("/admin/admin_exams")
def admin_exams():
    username = request.args.get("username")
    exams, redirect_resp = get_admin_data(username, "exams")
    if redirect_resp:
        return redirect_resp
    return render_template("admin/admin_exams.html", username=username, exams=exams)


@app.route("/admin/exams/<int:exam_id>")
def exams(exam_id):
    username = request.args.get("username")
    exam, redirect_resp = get_admin_data(
        username, "exams", single=True, where_clause="exam_id = ?", params=(exam_id,)
    )
    if redirect_resp:
        return redirect_resp
    return render_template("admin/exam.html", username=username, exams=exam)


@app.route("/admin/students")
def students():
    username = request.args.get("username")
    res, redirect_resp = get_admin_data(username, "student_profiles")
    if redirect_resp:
        return redirect_resp
    return render_template("admin/students.html", username=username, res=res)


@app.route("/admin/risk_analysis")
def risk_analysis():
    username = request.args.get("username")
    res, redirect_resp = get_admin_data(username, "risk_analysis")
    if redirect_resp:
        return redirect_resp
    return render_template("admin/risk_analysis.html", username=username, res=res)


@app.route("/admin/behavior_logs")
def behavior_logs():
    username = request.args.get("username")
    res, redirect_resp = get_admin_data(username, "behavior_logs")
    if redirect_resp:
        return redirect_resp
    return render_template("admin/behavior_logs.html", username=username, res=res)


@app.route("/admin/exams/<int:exam_id>/upload_csv", methods=["GET", "POST"])
def upload_csv(exam_id):
    username = request.args.get("username")
    if not username or not user_exists(username, "admin"):
        return redirect(url_for("login"))

    if request.method == "POST":
        file = request.files.get("csv_file")
        if file:
            import csv
            import sqlite3

            conn = sqlite3.connect("database/exam.db")
            cursor = conn.cursor()

            reader = csv.DictReader(file.stream.read().decode("utf-8").splitlines())

            try:
                for row in reader:
                    cursor.execute(
                        """INSERT INTO questions 
                        (exam_id, question_text, option_a, option_b, option_c, option_d, correct_option, wrong_answer_explanation, marks)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        (
                            exam_id,
                            row["question_text"],
                            row["option_a"],
                            row["option_b"],
                            row["option_c"],
                            row["option_d"],
                            row["correct_option"],
                            row.get("wrong_answer_explanation"),
                            row["marks"],
                        ),
                    )
                conn.commit()
                success = True
            except Exception as e:
                conn.rollback()
                success = False
                error_msg = str(e)
            finally:
                conn.close()

                exam_title = exams[0] if exams else "Unknown Exam"

            # You can now use `success` and `error_msg` in your template
            return render_template(
                "admin/upload_csv.html",
                username=username,
                exam_id=exam_id,
                success=success,
                error_msg=error_msg if not success else None,
            )

        # No file selected
        return render_template(
            "admin/upload_csv.html",
            username=username,
            exam_id=exam_id,
            success=False,
            error_msg="No file selected",
        )

    # GET request → show upload form
    return render_template(
        "admin/upload_csv.html", username=username, exam_id=exam_id, title=exam_title
    )


@app.route("/student/dashboard")
def student_dashboard():
    username = request.args.get("username")
    if not username or not user_exists(username, "student"):
        return redirect(url_for("login"))

    conn = sqlite3.connect("database/exam.db")
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT sp.photo_path
        FROM users u
        JOIN student_profiles sp ON u.user_id = sp.user_id
        WHERE u.username = ?
        """,
        (username,),
    )
    row = cursor.fetchone()
    conn.close()

    photo_path = row[0] if row else None
    return render_template(
        "student/student_dashboard.html", photo_path=photo_path, username=username
    )


# ---------------- Logout ----------------
@app.route("/logout")
def logout():
    return redirect(url_for("hello"))


if __name__ == "__main__":
    app.run(port=6969, debug=True)
