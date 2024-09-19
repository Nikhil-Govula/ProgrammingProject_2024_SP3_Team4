from flask import Blueprint, render_template, redirect, request

logins = Blueprint('logins', __name__)

@logins.route('/Login')
def index_user():
    return render_template('user/login_user.html')

@logins.route('/Admin/Login')
def index_admin():
    return render_template('admin/login_admin.html')

@logins.route('/Admin/')
def redirect_admin():
    return redirect("/Admin/Login", code=302)

@logins.route('/Company/Login')
def index_company():
    return render_template('company/login_company.html')

@logins.route('/Company/')
def redirect_company():
    return redirect("/Company/Login", code=302)
