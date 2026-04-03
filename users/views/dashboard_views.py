from rest_framework.views    import APIView
from rest_framework.response import Response
from rest_framework          import status
from datetime                import date, timedelta
from django.db.models        import Sum, Count
from django.db.models.functions import TruncMonth

from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes

from users.permissions  import IsAdminOrPersonnel
from clients.models     import Abonnement, Client
from produits.models    import Vente, Produit
from rest_framework.permissions import IsAuthenticated
from users.serializers import ChangePasswordSerializer
from users.services import AuthService
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from users.models import Utilisateur
# ══════════════════════════════════════════════════════════════════
# BLOC 1 — REVENUS
# GET /api/users/dashboard/revenus/?periode=7j|12m|tout
# ══════════════════════════════════════════════════════════════════




class DashboardRevenusView(APIView):
    permission_classes = [IsAdminOrPersonnel]

    @extend_schema(
        summary='Dashboard — Revenus',
        parameters=[
            OpenApiParameter(
                name='periode',
                type=str,
                location=OpenApiParameter.QUERY,
                description='Période courbe : 7j, 12m, tout',
                required=False,
            )
        ],
        responses={200: OpenApiTypes.OBJECT}
    )
    def get(self, request):
        aujourd_hui = date.today()
        debut_mois = aujourd_hui.replace(day=1)
        debut_annee = aujourd_hui.replace(month=1, day=1)
        periode = request.query_params.get('periode', '12m')

        MOIS_FR = {
            1: 'Jan', 2: 'Fév', 3: 'Mar', 4: 'Avr',
            5: 'Mai', 6: 'Jun', 7: 'Jul', 8: 'Aoû',
            9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Déc'
        }

        # ── Revenus jour
        abo_jour = Abonnement.objects.filter(
            est_paye=True, created_at__date=aujourd_hui
        ).aggregate(t=Sum('prix_paye'))['t'] or 0

        vente_jour = Vente.objects.filter(
            created_at__date=aujourd_hui
        ).aggregate(t=Sum('prix_total'))['t'] or 0

        # ── Revenus mois
        abo_mois = Abonnement.objects.filter(
            est_paye=True, created_at__date__gte=debut_mois
        ).aggregate(t=Sum('prix_paye'))['t'] or 0

        vente_mois = Vente.objects.filter(
            created_at__date__gte=debut_mois
        ).aggregate(t=Sum('prix_total'))['t'] or 0

        # ── Revenus année
        abo_annee = Abonnement.objects.filter(
            est_paye=True, created_at__date__gte=debut_annee
        ).aggregate(t=Sum('prix_paye'))['t'] or 0

        vente_annee = Vente.objects.filter(
            created_at__date__gte=debut_annee
        ).aggregate(t=Sum('prix_total'))['t'] or 0

        # ── Courbe revenus
        revenus_courbe = []

        if periode == '7j':
            for i in range(6, -1, -1):
                jour = aujourd_hui - timedelta(days=i)

                abo = Abonnement.objects.filter(
                    est_paye=True, created_at__date=jour
                ).aggregate(t=Sum('prix_paye'))['t'] or 0

                ven = Vente.objects.filter(
                    created_at__date=jour
                ).aggregate(t=Sum('prix_total'))['t'] or 0

                revenus_courbe.append({
                    'label': str(jour),
                    'abonnements': float(abo),
                    'ventes': float(ven),
                    'total': float(abo) + float(ven),
                })

        elif periode == '12m':
            annee = aujourd_hui.year

            for mois in range(1, 13):
                abo = Abonnement.objects.filter(
                    est_paye=True,
                    created_at__year=annee,
                    created_at__month=mois,
                ).aggregate(t=Sum('prix_paye'))['t'] or 0

                ven = Vente.objects.filter(
                    created_at__year=annee,
                    created_at__month=mois,
                ).aggregate(t=Sum('prix_total'))['t'] or 0

                revenus_courbe.append({
                    'label': f"{MOIS_FR[mois]} {annee}",
                    'abonnements': float(abo),
                    'ventes': float(ven),
                    'total': float(abo) + float(ven),
                })

        else:  # tout
            annee_actuelle = aujourd_hui.year

            for annee in range(2026, annee_actuelle + 1):
                abo = Abonnement.objects.filter(
                    est_paye=True, created_at__year=annee
                ).aggregate(t=Sum('prix_paye'))['t'] or 0

                ven = Vente.objects.filter(
                    created_at__year=annee
                ).aggregate(t=Sum('prix_total'))['t'] or 0

                revenus_courbe.append({
                    'label': str(annee),
                    'abonnements': float(abo),
                    'ventes': float(ven),
                    'total': float(abo) + float(ven),
                })

        # ── Stats globales
        if revenus_courbe:
            meilleur = max(revenus_courbe, key=lambda x: x['total'])
            moyenne = round(
                sum(r['total'] for r in revenus_courbe) / len(revenus_courbe), 2
            )
        else:
            meilleur = {'label': '-', 'total': 0}
            moyenne = 0

        # ── Revenus par pack (REMPLACE type)
        total_abonnements = Abonnement.objects.filter(est_paye=True).count()

        types = Abonnement.objects.filter(
            est_paye=True
        ).values('pack__nom').annotate(
            count=Count('id'),
            montant=Sum('prix_paye')
        ).order_by('-montant')

        revenus_par_type = [
            {
                'type': t['pack__nom'],  # ← important
                'label': t['pack__nom'],
                'count': t['count'],
                'montant': float(t['montant'] or 0),
                'pourcentage': round(
                    t['count'] / total_abonnements * 100, 1
                ) if total_abonnements > 0 else 0,
            }
            for t in types
        ]

        return Response({
            'revenu_jour': {
                'abonnements': float(abo_jour),
                'ventes': float(vente_jour),
                'total': float(abo_jour) + float(vente_jour),
            },
            'revenu_mois': {
                'abonnements': float(abo_mois),
                'ventes': float(vente_mois),
                'total': float(abo_mois) + float(vente_mois),
            },
            'revenu_annee': {
                'abonnements': float(abo_annee),
                'ventes': float(vente_annee),
                'total': float(abo_annee) + float(vente_annee),
            },
            'revenus_courbe': revenus_courbe,
            'meilleur_mois': meilleur,
            'moyenne_mensuelle': moyenne,
            'revenus_par_type': revenus_par_type,
        })

# ══════════════════════════════════════════════════════════════════
# BLOC 2 — ALERTES
# GET /api/users/dashboard/alertes/
# ══════════════════════════════════════════════════════════════════

class DashboardAlertesView(APIView):
    permission_classes = [IsAdminOrPersonnel]

    @extend_schema(
        summary   = 'Dashboard — Alertes',
        responses = {200: OpenApiTypes.OBJECT}
    )
    def get(self, request):

        # ── Abonnements expirant bientôt ─────────
        clients_vus = set()
        expirations_data = []

        expirations_qs = Abonnement.objects.filter(
            statut__in             = ['actif', 'en_attente'],
            seances_restantes__lte = 2,
            seances_restantes__gt  = 0,
        ).select_related('client').order_by('client_id', 'seances_restantes')

        for a in expirations_qs:
            if a.client_id not in clients_vus:
                clients_vus.add(a.client_id)
                expirations_data.append({
                    'client_nom'        : f"{a.client.prenom} {a.client.nom}",
                    'client_cin'        : a.client.cin,
                    'type': a.pack.nom if a.pack else 'inconnu',
                    'seances_restantes' : a.seances_restantes,
                })
            if len(expirations_data) >= 10:
                break

        # ── Stock faible ──────────────────────────
        stock_faible_qs = Produit.objects.filter(
            est_actif  = True,
            stock__lte = 2,
        ).order_by('stock')

        stock_faible_data = [
            {
                'id'           : str(p.id),
                'nom'          : p.nom,
                'type'         : p.get_type_display(),
                'stock'        : p.stock,
                'seuil_alerte' : p.seuil_alerte,
            }
            for p in stock_faible_qs
        ]

        return Response({
            'expirations_proches' : expirations_data,
            'expirations_count'   : len(expirations_data),
            'stock_faible'        : stock_faible_data,
            'stock_faible_count'  : len(stock_faible_data),
        })


# ══════════════════════════════════════════════════════════════════
# BLOC 3 — CLIENTS STATS
# GET /api/users/dashboard/clients/
# ══════════════════════════════════════════════════════════════════

class DashboardClientsView(APIView):
    permission_classes = [IsAdminOrPersonnel]

    @extend_schema(
        summary='Dashboard — Stats clients',
        responses={200: OpenApiTypes.OBJECT}
    )
    def get(self, request):
        aujourd_hui = date.today()
        debut_mois = aujourd_hui.replace(day=1)

        # ── Totaux clients ────────────────────────
        total_clients = Client.objects.count()

        nouveaux_mois = Client.objects.filter(
            created_at__date__gte=debut_mois
        ).count()

        clients_actifs = Client.objects.filter(
            abonnements__statut__in=['actif', 'en_attente']
        ).distinct().count()

        clients_inactifs = Client.objects.exclude(
            abonnements__statut__in=['actif', 'en_attente']
        ).distinct().count()

        # ── Abonnements par pack (ancien type) ───
        total_abonnements = Abonnement.objects.count()

        types = Abonnement.objects.values('pack__nom').annotate(
            count=Count('id')
        ).order_by('-count')

        abonnements_par_type = [
            {
                'type': t['pack__nom'],   # ← remplace type
                'label': t['pack__nom'],  # ← plus besoin de mapping
                'count': t['count'],
                'pourcentage': round(
                    t['count'] / total_abonnements * 100, 1
                ) if total_abonnements > 0 else 0,
            }
            for t in types
        ]

        return Response({
            'total_clients': total_clients,
            'nouveaux_mois': nouveaux_mois,
            'clients_actifs': clients_actifs,
            'clients_inactifs': clients_inactifs,
            'abonnements_par_type': abonnements_par_type,
        })
