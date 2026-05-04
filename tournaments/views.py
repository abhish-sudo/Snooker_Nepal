import urllib.parse
from django.shortcuts import render, get_object_or_404, redirect
from django.core.mail import send_mail
from django.conf import settings
from django.contrib import messages
from .models import Tournament, Registration
from .forms import RegistrationForm
from django.contrib.auth.decorators import login_required
from django.utils import timezone


def tournament_list(request):
    """Main calendar page — lists upcoming, ongoing, completed tournaments."""
    base_qs = Tournament.objects.filter(is_approved=True)

    # Filter by city if provided
    city_filter = request.GET.get('city', '').strip()
    if city_filter:
        base_qs = base_qs.filter(city__icontains=city_filter)

    upcoming  = base_qs.filter(status='upcoming').order_by('start_date')
    ongoing   = base_qs.filter(status='ongoing').order_by('start_date')
    completed = base_qs.filter(status='completed').order_by('-end_date')[:10]

    # Distinct city list for filter dropdown
    all_cities = (
        Tournament.objects
        .filter(is_approved=True)
        .values_list('city', flat=True)
        .distinct()
        .order_by('city')
    )

    return render(request, 'tournaments/list.html', {
        'upcoming':    upcoming,
        'ongoing':     ongoing,
        'completed':   completed,
        'all_cities':  all_cities,
        'city_filter': city_filter,
    })


def tournament_detail(request, pk):
    """Detail page with registration form."""
    tournament = get_object_or_404(Tournament, pk=pk, is_approved=True)
    form = RegistrationForm()
    duplicate = False

    today = timezone.now().date()

    if request.method == 'POST':
        if not (tournament.status == 'upcoming' and tournament.registration_deadline and tournament.registration_deadline >= today):
            messages.error(request, 'Registration for this tournament is closed.')
            return redirect('tournaments:detail', pk=pk)

        form = RegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            # Check for duplicate phone
            phone = form.cleaned_data['phone']
            if Registration.objects.filter(tournament=tournament, phone=phone).exists():
                duplicate = True
                form.add_error('phone', 'This number is already registered for this tournament.')
            else:
                reg = form.save(commit=False)
                reg.tournament = tournament
                reg.save()

                # Notify admin by email
                try:
                    send_mail(
                        subject=f'New Registration — {tournament.name}',
                        message=(
                            f'Name: {reg.full_name}\n'
                            f'Phone: {reg.phone}\n'
                            f'City: {reg.city}\n'
                            f'Age: {reg.age}\n'
                            f'Club/Hall: {reg.club_or_hall or "—"}\n'
                            f'Tournament: {tournament.name}\n'
                            f'Date: {tournament.start_date}\n'
                        ),
                        from_email=settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'noreply@snookernepal.com',
                        recipient_list=['info@snookernepal.com'],
                        fail_silently=True,
                    )
                except Exception:
                    pass  # Never crash registration because of email failure

                # Build WhatsApp confirmation URL
                wa_text = (
                    f"Hello! I just registered for *{tournament.name}*.\n"
                    f"Name: {reg.full_name}\n"
                    f"Phone: {reg.phone}\n"
                    f"City: {reg.city}"
                )
                wa_url = (
                    f"https://wa.me/977{tournament.contact_phone}"
                    f"?text={urllib.parse.quote(wa_text)}"
                )

                return render(request, 'tournaments/success.html', {
                    'tournament':   tournament,
                    'registration': reg,
                    'whatsapp_url': wa_url,
                })

    return render(request, 'tournaments/detail.html', {
        'tournament': tournament,
        'form':       form,
        'duplicate':  duplicate,
        'today':      today,
    })



@login_required
def submit_tournament(request):
    from .forms import TournamentSubmitForm
    
    if request.method == 'POST':
        form = TournamentSubmitForm(request.POST, request.FILES)
        if form.is_valid():
            tournament = form.save(commit=False)
            tournament.is_approved = False
            tournament.save()
            messages.success(request, 'Tournament submitted! It will appear after review.')
            return redirect('tournaments:list')
        else:
            print('FORM ERRORS:', form.errors)  # ← add this line
    else:
        form = TournamentSubmitForm()
    
    return render(request, 'tournaments/submit.html', {'form': form})