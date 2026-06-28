from django.shortcuts import render, redirect, get_object_or_404, reverse
from main.models import Publication, PublicationPayment
from main.Paystack import PayStack
from . import transaction_type

from django.conf import settings
from django.http import JsonResponse
from django.contrib import messages


import logging

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Create your views here.
def publication_view(requests):

    publication_payments = []
    if requests.user.is_authenticated:
       publication_payments = PublicationPayment.objects.filter(user = requests.user, approved=True).values_list('publication_id', flat=True)

    context = {
        'publications': Publication.objects.order_by('-uploadedAt').all(),
        'publication_payments': publication_payments,
    }
    return render(requests, 'publications.html', context)


def initiate_payment(request, publication_id):
    if request.method == 'POST':
        if not request.user.is_authenticated:
            return redirect('/login')
        
        publication = get_object_or_404(Publication, id=publication_id)
        publication_payment = PublicationPayment.objects.create(user = request.user, publication = publication)

        # Create payment on Paystack
        redirect_url = PayStack.generate_checkout_url(request.user.email,  publication.price * 100,
                                                       ref=publication_payment.id,
                                                       metadata={
                                                           'transaction_type': transaction_type.BOOK_PAYMENT,
                                                           'publication_id': publication_payment.id
                                                           })
        
        return redirect(redirect_url)
    
def verify_payment(request):
    # Get reference from the callback data
    reference = request.GET.get('reference')

    #get payment information
    payment_info = PayStack.verify_payment(reference)
    print(payment_info)

    if payment_info and payment_info['status'] == 'success':
        if payment_info.get('metadata').get('transaction_type') == transaction_type.BOOK_PAYMENT:
            publication_id = payment_info.get('metadata').get('publication_id')
            publication = PublicationPayment.objects.get(id=publication_id)
            publication.approved = True
            publication.save()
            messages.success(request, 'Successfully paid for publication, you can go ahead to download')
            return redirect(reverse('publication'))
        elif payment_info.get('metadata').get('transaction_type') == 'course_payment':
            return redirect(reverse('course:verify_payment') + f"?reference={reference}")
        else:
            messages.success(request, 'Thanks for making donations, God sees and rewards openly')
            return redirect('/')

    else: 
        messages.error(request, 'invalid payment')
        return redirect('/')

