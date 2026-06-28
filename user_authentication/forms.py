from django import forms
from django.forms import ModelForm 
from django.contrib.auth.forms import UserCreationForm

# import the model here to populate the form
from django.contrib.auth import get_user_model
User = get_user_model()

def validate_email(email):
    if not User.objects.filter(email = email).first():
        raise forms.ValidationError('Incorrect email or password')


def email_available(email):
    if User.objects.filter(email = email).first():
        raise forms.ValidationError('Email already taken. if yours, proceed to login')


class LoginForm(forms.Form):
    email = forms.EmailField(label='Email', max_length=70, validators= [validate_email])
    # username = forms.CharField(label='Username', max_length=100)
    password = forms.CharField(widget=forms.PasswordInput, min_length=6)

    email.widget.attrs.update({'class' : 'focus-visible:ring-offset-2', 'placeholder': 'email adress'})
    password.widget.attrs.update({'class' : 'focus-visible:ring-offset-2','placeholder': 'password'})


from .models import UserProfile

class RegisterForm(UserCreationForm):
    password1 = forms.CharField(required=True, widget = forms.PasswordInput(attrs={'class' : 'form-control', 'placeholder':'Password'}), label='Password')
    password2 = forms.CharField(required=True, widget = forms.PasswordInput(attrs={'class' : 'form-control', 'placeholder':'Comfirm password'}), label='Confirm Password')
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class':'form-control', 'placeholder':'Email adress', 'required': 'true'}),
            validators=[email_available])
    gender = forms.ChoiceField(choices=UserProfile.GENDER_CHOICES, widget=forms.Select(attrs={'class': 'form-control'}), label='Gender')
    interests = forms.ChoiceField(choices=UserProfile.INTEREST_CHOICES, widget=forms.Select(attrs={'class': 'form-control'}), label='Mentorship Focus Area')
    occupation = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Occupation'}), label='Occupation')
    location = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Location (e.g. Lagos, Nigeria)'}), label='Location')

    class Meta:
        model = User
        # specify field to be displayed from model here
        fields = ('first_name', 'last_name', 'email','password1', 'password2')
        widgets = {
            'email': forms.EmailInput(attrs={'class':'form-control', 'placeholder':'Email adress', 'required': 'true'}),
            'username': forms.TextInput(attrs={'class':'form-control', 'placeholder':'Username'}),
        }

    def __init__(self, *args, **kwargs):
        super(RegisterForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'focus-visible:ring-offset-2 form-control'


    def save(self, commit = True):
        user = super(RegisterForm, self).save(commit=False)
        user.email = self.cleaned_data.get('email')
        user.username = self.cleaned_data.get('email')
        if commit:
            user.save()
            UserProfile.objects.create(
                user=user,
                gender=self.cleaned_data.get('gender'),
                interests=self.cleaned_data.get('interests'),
                occupation=self.cleaned_data.get('occupation'),
                location=self.cleaned_data.get('location')
            )
        return user

