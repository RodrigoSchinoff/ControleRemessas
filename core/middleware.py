from django.http import HttpResponseForbidden
from django.utils.deprecation import MiddlewareMixin
from accounts.models import Membership

class CurrentOrgMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # padrão: sem org
        request.current_org = None
        request.current_membership = None

        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return  # público/anon, segue o fluxo (login, admin, static, etc.)

        # superuser pode passar sem membership (útil no /admin)
        if user.is_superuser:
            return

        # tenta achar membership ativa
        membership = (
            Membership.objects
            .select_related("organization")
            .filter(user=user, is_active=True)
            .first()
        )
        if not membership:
            return HttpResponseForbidden("Usuário sem organização ativa.")

        request.current_membership = membership
        request.current_org = membership.organization
