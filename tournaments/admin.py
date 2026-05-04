import csv
from django.contrib import admin
from django.http import HttpResponse
from django.utils.html import format_html
from .models import Tournament, Registration


@admin.register(Tournament)
class TournamentAdmin(admin.ModelAdmin):
    list_display   = ['name', 'city', 'start_date', 'end_date', 'status', 'spots_display', 'is_approved']
    list_filter    = ['status', 'is_approved', 'city', 'category', 'format']
    list_editable  = ['is_approved', 'status']
    search_fields  = ['name', 'city', 'venue_name']
    date_hierarchy = 'start_date'
    ordering       = ['start_date']
    actions        = ['approve_tournaments']

    fieldsets = (
        ('Basic Info', {
            'fields': ('name', 'format', 'category', 'status', 'is_approved')
        }),
        ('Location & Dates', {
            'fields': ('city', 'venue_name', 'venue_map_link', 'start_date', 'end_date', 'registration_deadline')
        }),
        ('Details', {
            'fields': ('entry_fee', 'prize_money', 'max_players', 'contact_phone', 'poster', 'description')
        }),
    )

    def spots_display(self, obj):
        left = obj.spots_left()
        color = '#27ae60' if left > 5 else ('#e67e22' if left > 0 else '#e74c3c')
        return format_html(
            '<span style="color:{}; font-weight:600;">{} / {}</span>',
            color, left, obj.max_players
        )
    spots_display.short_description = 'Spots Left'

    def approve_tournaments(self, request, queryset):
        updated = queryset.update(is_approved=True)
        self.message_user(request, f'{updated} tournament(s) approved.')
    approve_tournaments.short_description = 'Approve selected tournaments'


@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    list_display   = ['full_name', 'phone', 'city', 'age', 'tournament', 'is_paid', 'whatsapp_confirm_btn', 'registered_at']
    list_filter    = ['tournament', 'is_paid', 'city']
    list_editable  = ['is_paid']
    search_fields  = ['full_name', 'phone', 'city']
    ordering       = ['-registered_at']
    actions        = ['export_csv', 'mark_paid_and_notify']

    def whatsapp_confirm_btn(self, obj):
        
        import urllib.parse
        msg = (
            f"✅ Registration Confirmed!\n\n"
            f"Hello {obj.full_name},\n"
            f"Your registration for *{obj.tournament.name}* has been confirmed.\n\n"
            f"📍 Venue: {obj.tournament.venue_name}, {obj.tournament.city}\n"
            f"📱 Contact: +977 {obj.tournament.contact_phone}\n\n"
            f"Good luck! 🎱\n— Snooker Nepal"
        )
        wa_url = f"https://wa.me/977{obj.phone}?text={urllib.parse.quote(msg)}"
        return format_html(
            '<a href="{}" target="_blank" style="'
            'background:#25D366; color:white; padding:4px 10px; '
            'border-radius:4px; font-size:11px; font-weight:600; '
            'text-decoration:none; white-space:nowrap;">'
            '💬 Send WhatsApp</a>',
            wa_url
        )
    whatsapp_confirm_btn.short_description = 'Notify Player'

    def mark_paid_and_notify(self, request, queryset):
        updated = queryset.update(is_paid=True)
        self.message_user(
            request,
            f'{updated} registration(s) marked as paid. '
            f'Click the WhatsApp button next to each to notify them.'
        )
    mark_paid_and_notify.short_description = 'Mark selected as paid'

    def export_csv(self, request, queryset):
        import csv
        from django.http import HttpResponse
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="registrations.csv"'
        writer = csv.writer(response)
        writer.writerow(['Name', 'Phone', 'City', 'Age', 'Club/Hall', 'Tournament', 'Paid', 'Registered At'])
        for r in queryset:
            writer.writerow([
                r.full_name, r.phone, r.city, r.age,
                r.club_or_hall or '—',
                r.tournament.name,
                'Yes' if r.is_paid else 'No',
                r.registered_at.strftime('%Y-%m-%d %H:%M'),
            ])
        return response
    export_csv.short_description = 'Export selected to CSV'

    actions = ['export_csv', 'mark_paid_and_notify']