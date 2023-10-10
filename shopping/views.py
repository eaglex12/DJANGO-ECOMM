from django.shortcuts import render
from django.shortcuts import render, redirect
from django.views import View
from .forms import CustomerRegistration, Loginform,detailsform
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from . import models
from django.views.decorators.cache import cache_control
import razorpay
from django.conf import settings
from io import BytesIO
from django.http import HttpResponse
from xhtml2pdf import pisa

from django.template.loader import get_template
from django.core.mail import EmailMessage
from .models import order
from django.contrib.auth.decorators import login_required






# Create your views here.

def index1(request,category):
    if category=="all" or category==None:
        products= models.product.objects.all()
    else:
        products= models.product.objects.filter(product_category__name=category)
    n1= len(products)
    allCat= models.category.objects.all()
    n2= len(allCat)
    params={'param1':{'range':range(1,n1), 'product': products},
            'param2':{'range':range(1,n2), 'category': allCat}}
    params['nav_links'] = True

    if request.user.is_authenticated:
        cart_user= request.user
        cart_items= models.cart.objects.filter(user=cart_user)
        params['num_of_cart_items']=len(cart_items)
    else:
        params['cart_items']=0
    return render(request, 'home.html',params)

def index2(request):
    return redirect('home',category="all")


class register(View):
    def get(self,request):
        form = CustomerRegistration()
        return render(request,'register.html',{'form':form})
    def post(self,request):
        form = CustomerRegistration(request.POST)
        if form.is_valid():
            messages.success(request,'congratulations!! registered successfully')
            form.save()
        return render(request,'register.html',{'form':form}) 

def login(request):
    return render(request,'login.html')
def profile(request):
    return render(request,'profile.html')



def product(request,product_id):
    product_item= models.product.objects.filter(product_id=product_id)
    product_detail=product_item[0].product_details.split('_')
    if request.user.is_authenticated:
        cart_user= request.user
        cart_items= models.cart.objects.filter(user=cart_user)
        params={'product':product_item[0],'details':product_detail,'num_of_cart_items':len(cart_items)}
        params['nav_links']=True
        params['price_without_discount']=2000
        params['discount_percent']=(params['price_without_discount']-params['product'].product_price)/params['price_without_discount']*100
    return render(request,'product.html',params)


def cartView(request):
    params={'nav_links':True}
    if request.user.is_authenticated:
        cart_user= request.user
        cart_items= models.cart.objects.filter(user=cart_user)
        products=[]
        total_price=0
        for item in cart_items:
            product={
                'id':item.product_id.product_id,
                'name':item.product_id.product_title,
                'price':item.product_id.product_price*item.quantity,
                'quantity':item.quantity,
                'image':item.product_id.image,
                'category':item.product_id.product_category.name
            }
            total_price+=product['price']
            products.append(product)
        params['products']=products
        params['total_number_of_items']=len(products)
        params['total_price']=total_price
        params['shipping']=100
        params['total_amount']=total_price+100
        params['num_of_cart_items']=len(products)
        return render(request,'cart.html',params)
    else:
        return redirect('login')


@cache_control(no_cache=True, no_store=True)
def addtocart(request,product_id):
    cart_user= request.user
    cart_product= models.product.objects.filter(product_id=product_id)[0]
    if not models.cart.objects.filter(user=cart_user,product_id=cart_product).exists():            
        quantity=1
        #create new cart
        c=models.cart(user=cart_user,product_id=cart_product,quantity=quantity)
        c.save()
    else:
        #update cart
        cart_item= models.cart.objects.filter(user=cart_user,product_id=cart_product)[0]
        cart_item.quantity+=1
        cart_item.save()
    return redirect('cart')

def removefromcart(request,product_id):
    cart_user= request.user
    cart_product= models.product.objects.filter(product_id=product_id)[0]
    if models.cart.objects.filter(user=cart_user,product_id=cart_product)[0].quantity==1:          
        #delete cart
        cart_item= models.cart.objects.filter(user=cart_user,product_id=cart_product)[0]
        cart_item.delete()
    else:
        #update cart
        cart_item= models.cart.objects.filter(user=cart_user,product_id=cart_product)[0]
        cart_item.quantity-=1
        cart_item.save()
    return redirect('cart')



class addProfile(View):
    def get(self,request):
        form = detailsform()
        print(form)
        return render(request,'addprofile.html',{'form':form})
    def post(self,request):
        form = detailsform(request.POST)
        user= request.user
        form.instance.user_id=user
        if form.is_valid():
            form.save()
            return redirect('profile')
        return render(request,'addprofile.html',{'form':form})

class editProfile(View):
    def get(self,request):
        user= request.user
        details= models.billing_details.objects.filter(user_id=user)[0]
        form = detailsform(instance=details)
        return render(request,'addprofile.html',{'form':form})
    def post(self,request):
        user= request.user
        details= models.billing_details.objects.filter(user_id=user)[0]
        form = detailsform(request.POST,instance=details)
        if form.is_valid():
            form.save()
            return redirect('profile')
        return render(request,'addprofile.html',{'form':form})

def profile(request):
    params={'nav_links':True}
    if request.user.is_authenticated:
        user= request.user
        params['user']=user
        cart_items= models.cart.objects.filter(user=user)
        params['num_of_cart_items']=len(cart_items)
        if models.billing_details.objects.filter(user_id=user).exists():
            details= models.billing_details.objects.filter(user_id=user)[0]
            details={

                'name':details.name,
                'phone':details.phone,
                'email':details.email,
                'address':details.address,
                'city':details.city,
                'state':details.state,
                'pin':details.pin
            }
            params['details']=details
        else:
            params['details']=None
        return render(request,'profile.html',params)
    else:
        return redirect('login')



def checkout(request):
    params={'nav_links':True}
    if request.user.is_authenticated:
        params['ifDetails']=False
        if models.billing_details.objects.filter(user_id=request.user).exists():
            params['ifDetails']=True
        else:
            messages.warning(request,'Please add your details to proceed')
        total_price=0
        for item in models.cart.objects.filter(user=request.user):
            total_price+=item.product_id.product_price*item.quantity
        shipping=100
        total_amount=total_price+shipping
        params['total_price']=total_price
        params['shipping']=shipping
        params['total_amount']=total_amount

        user= request.user
        params['user']=user
        if models.billing_details.objects.filter(user_id=user).exists():
            details= models.billing_details.objects.filter(user_id=user)[0]
            details={

                'name':details.name,
                'phone':details.phone,
                'email':details.email,
                'address':details.address,
                'city':details.city,
                'state':details.state,
                'pin':details.pin
            }
            params['details']=details
        else:
            params['details']=None



        client = razorpay.Client(auth=(settings.KEY, settings.SECRET))
        order_amount = total_amount * 100  # Amount should be in paisa
        order_currency = 'INR'

        razorpay_order = client.order.create({
            'amount': order_amount,
            'currency': order_currency,
            'payment_capture': '1'
        })

        order_id = razorpay_order['id']

        params['order_id'] = order_id
        params['razorpay_key'] = settings.KEY

        return render(request, 'checkout.html', params)

def success(request):
    payment_id = request.GET.get('razorpay_payment_id')
    signature = request.GET.get('razorpay_signature')
    order_id = request.GET.get('razorpay_order_id')
    
    client = razorpay.Client(auth=(settings.KEY, settings.SECRET))
    payment = client.payment.fetch(payment_id)

    user = request.user
    billing_details = models.billing_details.objects.get(user_id=user)

    payment_details = {
        'order_id': order_id,
        'payment_id': payment_id,
        'signature': signature,
        'amount': payment['amount'],
        'currency': payment['currency'],
        'status': payment['status'],
        'method': payment['method'],
        'email': payment['email'],
           # Add billing address details
        'billing_name': billing_details.name,
        'billing_email': billing_details.email,
        'billing_address': billing_details.address,
        'billing_city': billing_details.city,
        'billing_state': billing_details.state,
        'billing_pin': billing_details.pin,
        'billing_phone': billing_details.phone,

        # Add more details as needed
    }

    print(payment_details)
    pdf_content = generate_pdf('invoice.html', {'payment_details': payment_details})

    # Save Order
    cart_items = models.cart.objects.filter(user=user)
    billing_detail = models.billing_details.objects.get(user_id=user)



    order = models.order.objects.create(
        cart_id=cart_items[0],  # Assuming one cart item per order for simplicity
        billing_detail=billing_detail,
        payment_status=True,  # Set payment status based on your logic
        razor_pay_order_id=order_id,
        razor_pay_payment_id=payment_id,
        razor_pay_signature_id=signature,
        total_amount_paid=payment_details['amount']  # Add this line to update total amount paid

    )

    to_email = request.user.email

    # Send Email
    subject = 'Invoice for Your Purchase'
    message = 'Thank you for your purchase. Please find the attached invoice.'
    send_invoice_email(to_email, subject, message, pdf_content)

    


    response = HttpResponse(pdf_content, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="invoice.pdf"'
    return redirect('checkout')



# Updated generate_pdf function
def generate_pdf(template_path, context):
    template = get_template(template_path)
    html = template.render(context)
    pdf_content = BytesIO()

    # Generate the PDF
    pisa_status = pisa.CreatePDF(html, dest=pdf_content)

    if pisa_status.err:
        return None

    pdf_content.seek(0)
    return pdf_content.getvalue()


def send_invoice_email(to_email, subject, message, pdf_content):
    email = EmailMessage(subject, message, 'your_email@example.com', [to_email])
    email.attach('invoice.pdf', pdf_content, 'accounts/pdf')
    email.send()

@login_required

def display_orders(request):
    user_orders = order.objects.filter(cart_id__user=request.user)

    context = {'orders': user_orders}  # Create a context with the user-specific orders
    return render(request, 'orders.html', context)