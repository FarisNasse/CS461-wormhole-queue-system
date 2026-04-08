from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField, FileRequired
from wtforms import (
    BooleanField,
    DateField,
    IntegerField,
    PasswordField,
    SelectField,
    StringField,
    SubmitField,
)
from wtforms.validators import DataRequired, Email, EqualTo, NumberRange, Optional


class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember_me = BooleanField("Remember Me")
    submit = SubmitField("Sign In")


class TicketForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    phClass = SelectField(
        "Class",
        choices=[
            ("Ph 211", "Ph 211"),
            ("Ph 212", "Ph 212"),
            ("Ph 213", "Ph 213"),
            ("Ph 20x", "Ph 20x"),
            ("Ph 20x Ecampus", "Ph 20x Ecampus"),
            ("Ph 21x Ecampus", "Ph 21x Ecampus"),
        ],
        validators=[DataRequired()],
    )
    location = SelectField(
        "Location",
        choices=[("Teams", "Teams"), ("Zoom", "Zoom")],
        validators=[DataRequired()],
    )
    submit = SubmitField("Create")


class RegisterForm(FlaskForm):
    first_name = StringField("First Name", validators=[DataRequired()])
    last_name = StringField("Last Name", validators=[DataRequired()])
    onid = StringField("ONID", validators=[DataRequired()])
    is_admin = BooleanField("Administrator")
    submit = SubmitField("Create")


class RegisterBatchForm(FlaskForm):
    user_csv = FileField(
        "User CSV",
        validators=[FileRequired(), FileAllowed(["csv"], "Please upload a CSV file.")],
    )
    submit = SubmitField("Register Batch")


class ResetPasswordRequestForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    submit = SubmitField("Request Reset")


class ResetPasswordForm(FlaskForm):
    password = PasswordField("New Password", validators=[DataRequired()])
    password2 = PasswordField(
        "Re-enter Password", validators=[DataRequired(), EqualTo("password")]
    )
    submit = SubmitField("Change Password")


class DeleteUserForm(FlaskForm):
    confirm = StringField('Type "DELETE" to confirm', validators=[DataRequired()])
    submit = SubmitField("Confirm")


class ChangePassForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    old_password = PasswordField("Old Password", validators=[DataRequired()])
    password = PasswordField("New Password", validators=[DataRequired()])
    password2 = PasswordField(
        "Re-enter New Password", validators=[DataRequired(), EqualTo("password")]
    )
    submit = SubmitField("Change Password")


class EditUserForm(FlaskForm):
    first_name = StringField("First Name", validators=[Optional()])
    last_name = StringField("Last Name", validators=[Optional()])
    onid = StringField("ONID", validators=[Optional()])
    email = StringField("Email", validators=[Optional(), Email()])
    is_admin = SelectField(
        "Is Admin",
        choices=[
            ("", "Update"),
            ("true", "True"),
            ("false", "False"),
        ],
        validators=[Optional()],
    )
    is_active = SelectField(
        "Is Active",
        choices=[
            ("", "Update"),
            ("true", "True"),
            ("false", "False"),
        ],
        validators=[Optional()],
    )
    submit = SubmitField("Update")


class ResolveTicketForm(FlaskForm):
    numStds = IntegerField(
        "Number of Students", validators=[Optional(), NumberRange(min=1)]
    )
    resolveReason = SelectField(
        "Resolution Reason",
        choices=[
            ("helped", "Helped"),
            ("no_show", "No Show"),
            ("duplicate", "Duplicate"),
        ],
        validators=[DataRequired(message="Please select a reason.")],
    )
    submit = SubmitField("Submit")


class ExportArchiveForm(FlaskForm):
    start_date = DateField("Start Date", validators=[DataRequired()])
    end_date = DateField("End Date", validators=[DataRequired()])
    submit = SubmitField("Download CSV")


class FlushQueueForm(FlaskForm):
    """Simple form to handle CSRF protection for the Flush Queue action."""

    submit = SubmitField("Flush Queue")


class ClearQueueForm(FlaskForm):
    """Simple form to handle CSRF protection for the Clear Queue action."""

    submit = SubmitField("Clear Queue")
