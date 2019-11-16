from crispy_forms.helper import FormHelper
from yoloify.signup.forms import LoginForm, SignupForm, PasswordResetForm, ConfirmationResendForm


def auth_forms(request):
    login_form = LoginForm()
    login_form.helper = FormHelper()
    login_form.helper.form_tag = False

    signup_form = SignupForm()
    signup_form.helper = FormHelper()
    signup_form.helper.form_tag = False

    reset_form = PasswordResetForm()
    reset_form.helper = FormHelper()
    reset_form.helper.form_tag = False

    resend_form = ConfirmationResendForm()
    resend_form.helper = FormHelper()
    resend_form.helper.form_tag = False

    return {
        'login_shortcut': login_form,
        'signup_shortcut': signup_form,
        'reset_shortcut': reset_form,
        'resend_shortcut': resend_form
    }
