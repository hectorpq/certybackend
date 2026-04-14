from django.contrib import admin
from django.utils.html import format_html
from django.contrib import messages
from django.core.exceptions import ValidationError
from .models import Template, Certificate

# Constants
_STATUS_BADGE_STYLE = '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>'


@admin.register(Template)
class TemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'status_badge', 'usage_count', 'created_by', 'created_at')
    list_filter = ('is_active', 'category', 'created_at')
    search_fields = ('name', 'category')
    readonly_fields = ('id', 'created_at', 'updated_at', 'preview_image')
    
    fieldsets = (
        ('Template Information', {
            'fields': ('id', 'name', 'category')
        }),
        ('Assets', {
            'fields': ('background_url', 'preview_image')
        }),
        ('Configuration', {
            'fields': ('layout_config',)
        }),
        ('Management', {
            'fields': ('is_active', 'created_by')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    ordering = ['-created_at']
    date_hierarchy = 'created_at'

    def status_badge(self, obj):
        color = 'green' if obj.is_active else 'red'
        status = 'Active' if obj.is_active else 'Inactive'
        return format_html(
            _STATUS_BADGE_STYLE,
            color,
            status
        )
    status_badge.short_description = 'Status'

    def usage_count(self, obj):
        count = obj.certificates.count()
        return format_html('<b>{}</b>', count)
    usage_count.short_description = 'Used'

    def preview_image(self, obj):
        if obj.preview_url:
            return format_html('<img src="{}" width="300" />', obj.preview_url)
        return "No preview available"
    preview_image.short_description = 'Preview'


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    # Constants
    _CERT_INFO_LABEL = 'Certificate Information'
    _STUDENT_EVENT_LABEL = 'Student & Event'
    
    list_display = ('student_name', 'event_name', 'verification_code_short', 'status_badge', 'delivery_badge', 'issued_at')
    list_filter = ('status', 'issued_at', 'template', 'event__category')
    search_fields = ('student__first_name', 'student__last_name', 'student__email', 'verification_code', 'event__name')
    actions = ['generate_certificates', 'deliver_certificates', 'deliver_whatsapp', 'deliver_link', 'mark_as_failed_action', 'reset_to_pending']
    
    fieldsets = (
        (_CERT_INFO_LABEL, {
            'fields': ('id', 'verification_code_info', 'status')
        }),
        (_STUDENT_EVENT_LABEL, {
            'fields': ('student', 'event')
        }),
        ('Template', {
            'fields': ('template', 'template_info')
        }),
        ('PDF & Generation', {
            'fields': ('pdf_url', 'generated_by')
        }),
        ('Delivery Tracking', {
            'fields': ('delivery_history',),
            'classes': ('collapse',)
        }),
        ('Expiration', {
            'fields': ('expires_at',)
        }),
        ('Timestamps', {
            'fields': ('issued_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        """Student and event are editable only during creation"""
        base_readonly = ('id', 'issued_at', 'updated_at', 'verification_code_info', 'template_info', 'delivery_history')
        
        # During edit (obj exists), student and event become readonly
        if obj:
            return base_readonly + ('student', 'event')
        
        # During creation, they are editable
        return base_readonly
    
    def get_fieldsets(self, request, obj=None):
        """Show different fieldsets during creation vs editing"""
        if obj:
            # During edit, show all fields with verification code info
            return [
                (self._CERT_INFO_LABEL, {
                    'fields': ('id', 'verification_code_info', 'status')
                }),
                (self._STUDENT_EVENT_LABEL, {
                    'fields': ('student', 'event')
                }),
                ('Template', {
                    'fields': ('template', 'template_info')
                }),
                ('PDF & Generation', {
                    'fields': ('pdf_url', 'generated_by')
                }),
                ('Delivery Tracking', {
                    'fields': ('delivery_history',),
                    'classes': ('collapse',)
                }),
                ('Expiration', {
                    'fields': ('expires_at',)
                }),
                ('Timestamps', {
                    'fields': ('issued_at', 'updated_at'),
                    'classes': ('collapse',)
                }),
            ]
        else:
            # During creation, skip timestamps and delivery tracking
            return [
                (self._CERT_INFO_LABEL, {
                    'fields': ('status',),
                    'description': 'The verification code will be generated automatically.'
                }),
                (self._STUDENT_EVENT_LABEL, {
                    'fields': ('student', 'event'),
                    'description': 'Select the student and event for this certificate.'
                }),
                ('Template', {
                    'fields': ('template',)
                }),
                ('Expiration', {
                    'fields': ('expires_at',)
                }),
            ]

    ordering = ['-issued_at']
    date_hierarchy = 'issued_at'

    def student_name(self, obj):
        return f"{obj.student.first_name} {obj.student.last_name}"
    student_name.short_description = 'Student'

    def event_name(self, obj):
        return obj.event.name
    event_name.short_description = 'Event'

    def status_badge(self, obj):
        colors = {
            'pending': 'orange',
            'generated': 'blue',
            'sent': 'green',
            'failed': 'red'
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            _STATUS_BADGE_STYLE,
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    def delivery_badge(self, obj):
        """Show delivery status based on latest delivery log"""
        if not obj.has_delivery_attempts():
            return format_html('<span style="color: gray;">N/A</span>')
        
        last_delivery = obj.last_delivery_attempt
        colors = {
            'success': 'green',
            'error': 'red',
            'pending': 'orange'
        }
        color = colors.get(last_delivery.status, 'gray')
        return format_html(
            _STATUS_BADGE_STYLE,
            color,
            last_delivery.get_delivery_method_display()
        )
    delivery_badge.short_description = 'Last Delivery'

    def verification_code_short(self, obj):
        code = obj.verification_code or "Not generated"
        if len(code) > 15:
            return f"{code[:15]}..."
        return code
    verification_code_short.short_description = 'Verification Code'

    def verification_code_info(self, obj):
        code = obj.verification_code or "Not generated yet"
        return format_html(
            '<code style="background-color: #f0f0f0; padding: 5px; border-radius: 3px; font-weight: bold;">{}</code>',
            code
        )
    verification_code_info.short_description = 'Verification Code'

    def student_info(self, obj):
        return format_html(
            '<b>{}</b><br/>Document: {}<br/>Email: {}',
            obj.student.full_name,
            obj.student.document_id,
            obj.student.email
        )
    student_info.short_description = 'Student'

    def event_info(self, obj):
        return format_html(
            '<b>{}</b><br/>Date: {}<br/>Category: {}',
            obj.event.name,
            obj.event.event_date.strftime('%d/%m/%Y'),
            obj.event.category.name if obj.event.category else 'N/A'
        )
    event_info.short_description = 'Event'

    def template_info(self, obj):
        if obj.template:
            url = obj.pdf_url or "#"
            download_btn = format_html(
                '<a href="{}" target="_blank" style="color: #0066cc; text-decoration: none;">📥 Download PDF</a>',
                url
            ) if obj.pdf_url else "PDF not available"
            return format_html(
                '<b>{}</b><br/>Category: {}<br/>{}',
                obj.template.name,
                obj.template.category or 'N/A',
                download_btn
            )
        return "No template assigned"
    template_info.short_description = 'Template'

    def delivery_history(self, obj):
        """Show all delivery attempts"""
        deliveries = obj.get_delivery_history()
        if not deliveries:
            return "No delivery attempts yet"
        
        html_list = []
        for delivery in deliveries:
            icon = delivery.get_status_icon()
            method_icon = delivery.get_delivery_icon()
            method = delivery.get_delivery_method_display()
            timestamp = delivery.sent_at.strftime('%d/%m/%Y %H:%M')
            
            html_list.append(
                f"<li>{icon} {method_icon} {method} → {delivery.recipient} ({timestamp})</li>"
            )
        
        return format_html(
            '<ul style="list-style: none; padding: 0;">{}</ul>',
            ''.join(html_list)
        )
    delivery_history.short_description = 'Delivery History'

    # ========== CUSTOM ADMIN ACTIONS ==========

    def generate_certificates(self, request, queryset):
        """Action: Generate pending certificates"""
        generated = 0
        
        for certificate in queryset.filter(status='pending'):
            try:
                # Check if enrollment exists and student attended
                from events.models import Enrollment
                try:
                    enrollment = Enrollment.objects.get(
                        student=certificate.student,
                        event=certificate.event
                    )
                    if not enrollment.attendance:
                        self.message_user(
                            request,
                            f"⚠️  {certificate.student.first_name}: No attendance record",
                            messages.WARNING
                        )
                        continue
                except Enrollment.DoesNotExist:
                    self.message_user(
                        request,
                        f"⚠️  {certificate.student.first_name}: Not enrolled in event",
                        messages.WARNING
                    )
                    continue
                
                # Generate certificate
                certificate.generate(
                    template=certificate.template,
                    generated_by=request.user
                )
                generated += 1
            except ValidationError as e:
                self.message_user(request, f"❌ Error: {e.message}", messages.ERROR)
        
        if generated > 0:
            self.message_user(
                request,
                f"✅ {generated} certificates generated successfully",
                messages.SUCCESS
            )
    
    generate_certificates.short_description = "✅ Generate Certificates (pending only)"

    def deliver_certificates(self, request, queryset):
        """Action: Deliver generated certificates via email (REAL EMAIL)"""
        delivered = 0
        failed = 0
        errors = []
        
        for certificate in queryset.filter(status__in=['generated', 'sent']):
            try:
                # Deliver via REAL email
                delivery_log = certificate.deliver(
                    method='email',
                    recipient=certificate.student.email,
                    sent_by=request.user
                )
                
                if delivery_log.status == 'success':
                    delivered += 1
                else:
                    failed += 1
                    if delivery_log.error_message:
                        errors.append(f"{certificate.student.first_name}: {delivery_log.error_message}")
                    
            except ValidationError as e:
                self.message_user(request, f"❌ Validation Error: {str(e)}", messages.ERROR)
                failed += 1
            except Exception as e:
                self.message_user(request, f"❌ Unexpected Error: {str(e)}", messages.ERROR)
                failed += 1
        
        # Summary message
        if delivered > 0:
            self.message_user(
                request,
                f"📧 {delivered} certificates delivered via EMAIL successfully",
                messages.SUCCESS
            )
        
        if failed > 0:
            error_detail = "\n".join(errors[:3]) if errors else "Check email configuration"
            self.message_user(
                request,
                f"⚠️  {failed} delivery failures. {error_detail}",
                messages.WARNING
            )
    
    deliver_certificates.short_description = "📧 Deliver via Email (REAL EMAIL)"

    def mark_as_failed_action(self, request, queryset):
        """Action: Mark certificates as failed (only generated/sent/failed)"""
        # Filter out pending certificates (can't fail what hasn't been generated)
        valid_certs = queryset.exclude(status='pending')
        
        if not valid_certs.exists():
            self.message_user(
                request,
                "⚠️ Cannot mark pending certificates as failed - select generated or sent certificates only",
                messages.WARNING
            )
            return
        
        for certificate in valid_certs:
            try:
                certificate.mark_as_failed(
                    error_message="Marked as failed from admin",
                    sent_by=request.user
                )
            except ValidationError:
                pass  # Already filtered, but just in case
        
        self.message_user(
            request,
            f"❌ {valid_certs.count()} certificates marked as failed",
            messages.WARNING
        )
    
    mark_as_failed_action.short_description = "❌ Mark as Failed (generated/sent only)"

    def reset_to_pending(self, request, queryset):
        """Action: Reset certificates to pending (for retry workflows)"""
        count = queryset.update(status='pending')
        self.message_user(
            request,
            f"↩️  {count} certificates reset to pending",
            messages.INFO
        )
    
    reset_to_pending.short_description = "↩️  Reset to Pending (for retry)"

    def deliver_whatsapp(self, request, queryset):
        """Action: Deliver certificates via WhatsApp (REAL WHATSAPP)"""
        delivered = 0
        failed = 0
        errors = []
        
        for certificate in queryset.filter(status__in=['generated', 'sent']):
            try:
                # Check if student has phone
                if not certificate.student.phone:
                    self.message_user(
                        request,
                        f"⚠️  {certificate.student.first_name}: No phone number on file",
                        messages.WARNING
                    )
                    failed += 1
                    continue
                
                # Deliver via REAL WhatsApp
                delivery_log = certificate.deliver(
                    method='whatsapp',
                    recipient=certificate.student.phone,
                    sent_by=request.user
                )
                
                if delivery_log.status == 'success':
                    delivered += 1
                else:
                    failed += 1
                    if delivery_log.error_message:
                        errors.append(f"{certificate.student.first_name}: {delivery_log.error_message}")
                    
            except ValidationError as e:
                self.message_user(request, f"❌ Error: {str(e)}", messages.ERROR)
                failed += 1
        
        if delivered > 0:
            self.message_user(
                request,
                f"💬 {delivered} certificates delivered via WhatsApp",
                messages.SUCCESS
            )
        
        if failed > 0:
            error_detail = "\n".join(errors[:3]) if errors else "Check Twilio configuration"
            self.message_user(
                request,
                f"⚠️  {failed} failures. {error_detail}",
                messages.WARNING
            )
    
    deliver_whatsapp.short_description = "💬 Deliver via WhatsApp (REAL WHATSAPP)"

    def deliver_link(self, request, queryset):
        """Action: Deliver certificates via direct link"""
        delivered = 0
        
        for certificate in queryset.filter(status__in=['generated', 'sent']):
            try:
                # Deliver via link (no email needed)
                delivery_log = certificate.deliver(
                    method='link',
                    recipient=None,  # Link doesn't need recipient
                    sent_by=request.user
                )
                
                if delivery_log.status == 'success':
                    delivered += 1
                    
            except ValidationError as e:
                self.message_user(request, f"❌ Error: {str(e)}", messages.ERROR)
        
        if delivered > 0:
            self.message_user(
                request,
                f"🔗 {delivered} certificates marked as delivered (direct link)",
                messages.SUCCESS
            )
    
    deliver_link.short_description = "🔗 Mark as Delivered (Direct Link)"
