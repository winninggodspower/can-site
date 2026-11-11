from django.shortcuts import render, redirect
from django.contrib import messages
from main.forms import MeetingReportForm
from publication import transaction_type
from .models import About, Announcement, Gallery, Giving, MeetingReport, Welfare, Publication, Event
from .Paystack import PayStack

# Create your views here.


def home(requests):
    # Prefer featured event, fallback to latest created event
    featured_event = Event.objects.filter(is_featured=True).order_by('-date_created').first()
    latest_event = featured_event or Event.objects.order_by('-date_created').first()

    context = {
        'featured_event': featured_event,
        'latest_event': latest_event,
        'announcements' : list(Announcement.objects.all()),
    }
    return render(requests, 'index.html', context)

def about_view(requests):
    return render(requests, 'aboutus.html')

def gallery_view(requests):
    context = {
        'gallery': Gallery.objects.all()
    }
    return render(requests, 'gallery.html', context)

def partner_view(requests):
    meeting_form = MeetingReportForm()
    return render(requests, 'partners.html', {'meeting_form': meeting_form})

def meeting_view(request):
    if request.method == 'POST':
        meeting_form = MeetingReportForm(request.POST)
        if meeting_form.is_valid():
            meeting_form.save()  # This will automatically save the form data into the MeetingReport model
            messages.success(request, 'Successfully saved the meeting report and sent it to all admins.')
            return redirect('/partner')
        else:
            messages.error(request, 'Please correct the errors below.')
    
    else:
        meeting_form = MeetingReportForm()
    
    return render(request, 'partners.html', {'meeting_form': meeting_form})

def meeting_admin_view(request):
    if not request.user.is_staff:
        messages.error(request, "Only admins can access this page.")
        return redirect('/login')
    
    reports = MeetingReport.objects.all().order_by('-date')
    return render(request, 'admin_meeting_report.html', {'reports': reports})


def welfare_view(request):
    if request.method == 'POST':
        welfare_member_name = request.POST.get('memberName')
        welfare_report_details = request.POST.get('welfareDetails')

        if not welfare_member_name or not welfare_report_details:
            messages.error(request, 'please fill in the member\'s name and details field accordinly')
            return redirect('/partner')
        
        messages.success(request, 'successfully saved welfare report and has been sent to all admins')
        Welfare.objects.create(member_name=welfare_member_name, details=welfare_report_details)

    return redirect('/partner')

def giving_view(requests):
    if requests.method == 'POST':
        email = requests.user.email if requests.user.is_authenticated else "unknown@gmail.com"

        amount = int(requests.POST.get('amount'))
        message = requests.POST.get('message')
        currency = requests.POST.get('currency')
        print(currency)

        redirect_url = PayStack.generate_checkout_url(email,  amount * 100, 
                                                      currency=currency,  
                                                      metadata={'transaction_type': transaction_type.GIVING})
        
        if redirect_url:
            # save infor to database
            Giving.objects.create(amount = amount, message = message)
            return redirect(redirect_url)
        else: 
            messages.error(requests, "something went wrong, please try selecting another curreny")
    return render(requests, 'giving.html')

def verify_giving_callback(requests):
    reference = requests.GET.get('reference')
    messages.success(requests, 'Thanks for making donations, God sees and rewards openly')
    return redirect('/')

def events_view(requests):
    context = {
        "events": Event.objects.all(),
    }
    return render(requests, 'upcoming.html', context)


def login_view(requests):
    return render(requests, 'login.html')

def signup_view(requests):
    return render(requests, 'signup.html')