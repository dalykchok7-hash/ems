from rest_framework.views    import APIView
from rest_framework.response import Response
from rest_framework          import status
from datetime                import date, timedelta
from django.db.models        import Sum, Count,Min
from django.db.models.functions import TruncMonth, TruncDate

from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from users.permissions  import IsAdminOrPersonnel
from clients.models     import Abonnement, Client
from produits.models    import Vente
from seances.models     import Seance, Reservation


class DashboardStatsView(APIView):
    permission_classes = [IsAdminOrPersonnel]

    @extend_schema(
        summary    = 'Statistiques dashboard',
        parameters = [
            OpenApiParameter(
                name        = 'periode',
                type        = str,
                location    = OpenApiParameter.QUERY,
                description = 'Période courbe revenus : 7j, 12m, tout',
                required    = False,
            )
        ],
        responses  = {200: OpenApiTypes.OBJECT}
    )
    def get(self, request):
        aujourd_hui = date.today()
        debut_mois  = aujourd_hui.replace(day=1)
        debut_annee = aujourd_hui.replace(month=1, day=1)
        periode     = request.query_params.get('periode', '12m')

        # ── Revenus abonnements ──────────────────
        abo_jour  = Abonnement.objects.filter(
            est_paye         = True,
            created_at__date = aujourd_hui
        ).aggregate(total=Sum('prix_paye'))['total'] or 0

        abo_mois  = Abonnement.objects.filter(
            est_paye              = True,
            created_at__date__gte = debut_mois
        ).aggregate(total=Sum('prix_paye'))['total'] or 0

        abo_annee = Abonnement.objects.filter(
            est_paye              = True,
            created_at__date__gte = debut_annee
        ).aggregate(total=Sum('prix_paye'))['total'] or 0

        # ── Revenus ventes ───────────────────────
        vente_jour  = Vente.objects.filter(
            created_at__date = aujourd_hui
        ).aggregate(total=Sum('prix_total'))['total'] or 0

        vente_mois  = Vente.objects.filter(
            created_at__date__gte = debut_mois
        ).aggregate(total=Sum('prix_total'))['total'] or 0

        vente_annee = Vente.objects.filter(
            created_at__date__gte = debut_annee
        ).aggregate(total=Sum('prix_total'))['total'] or 0

        # ── Totaux ───────────────────────────────
        revenu_jour  = float(abo_jour)  + float(vente_jour)
        revenu_mois  = float(abo_mois)  + float(vente_mois)
        revenu_annee = float(abo_annee) + float(vente_annee)

        # ── Clients actifs ───────────────────────
        clients_actifs = Client.objects.filter(
            abonnements__statut__in=['actif', 'en_attente']
        ).distinct().count()

        # ── Expirations proches ──────────────────
        expirations_qs = Abonnement.objects.filter(
            statut__in             = ['actif', 'en_attente'],
            seances_restantes__lte = 2,
            seances_restantes__gt  = 0,
        ).select_related('client').order_by('client_id', 'seances_restantes')

        clients_vus = set()
        expirations_data = []

        for a in expirations_qs:
            if a.client_id not in clients_vus:
                clients_vus.add(a.client_id)
                expirations_data.append({
                    'client_nom'        : f"{a.client.prenom} {a.client.nom}",
                    'client_cin'        : a.client.cin,
                    'type'              : a.get_type_display(),
                    'seances_restantes' : a.seances_restantes,
        })
            if len(expirations_data) >= 10:
                break

        # ── Séances aujourd'hui ──────────────────
        seances_jour = Seance.objects.filter(
            date = aujourd_hui
        ).order_by('heure_debut')

        total_places      = sum(s.places_total       for s in seances_jour)
        places_occupees   = sum(
            s.places_total - s.places_disponibles for s in seances_jour
        )
        taux_remplissage  = round(
            (places_occupees / total_places * 100), 1
        ) if total_places > 0 else 0

        seances_aujourd_hui = seances_jour.count()

        # ── Séances du jour tableau ──────────────
        seances_data = []
        for s in seances_jour:
            reservations = s.reservations.filter(
                statut__in=['en_attente', 'present']
            )
            i_motion = reservations.filter(type_appareil='i-motion').count()
            i_model  = reservations.filter(type_appareil='i-model').count()
            occupees = s.places_total - s.places_disponibles

            if occupees == s.places_total:
                statut_seance = 'complet'
            elif occupees >= s.places_total - 1:
                statut_seance = 'bientot_plein'
            else:
                statut_seance = 'disponible'

            seances_data.append({
                'id'                 : str(s.id),
                'heure_debut'        : str(s.heure_debut),
                'heure_fin'          : str(s.heure_fin),
                'reservations'       : occupees,
                'places_total'       : s.places_total,
                'places_disponibles' : s.places_disponibles,
                'i_motion'           : i_motion,
                'i_model'            : i_model,
                'taux'               : round(occupees / s.places_total * 100, 0) if s.places_total > 0 else 0,
                'statut'             : statut_seance,
            })

        # ── Courbe revenus ───────────────────────
        revenus_courbe = []
        MOIS_FR = {
            1: 'Jan', 2: 'Fév', 3: 'Mar', 4: 'Avr',
            5: 'Mai', 6: 'Jun', 7: 'Jul', 8: 'Aoû',
            9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Déc'
        }

        if periode == '7j':
            for i in range(6, -1, -1):
                jour = aujourd_hui - timedelta(days=i)
                abo  = Abonnement.objects.filter(
                    est_paye=True, created_at__date=jour
                ).aggregate(t=Sum('prix_paye'))['t'] or 0
                ven  = Vente.objects.filter(
                     created_at__date=jour
                ).aggregate(t=Sum('prix_total'))['t'] or 0
                revenus_courbe.append({
                    'label'  : jour.strftime('%d %b').replace(
                        'Apr','Avr').replace('May','Mai').replace(
                        'Aug','Aoû').replace('Oct','Oct'),
                    'montant': float(abo) + float(ven)
                })

        elif periode == '12m':
            annee = aujourd_hui.year
            for mois in range(1, 13):
                abo = Abonnement.objects.filter(
                    est_paye              = True,
                    created_at__year      = annee,
                    created_at__month     = mois,
                ).aggregate(t=Sum('prix_paye'))['t'] or 0
                ven = Vente.objects.filter(
                    created_at__year  = annee,
                    created_at__month = mois,
                ).aggregate(t=Sum('prix_total'))['t'] or 0
                revenus_courbe.append({
                    'label'  : f"{MOIS_FR[mois]} {annee}",
                    'montant': float(abo) + float(ven)
                })

        else:  # tout
            annee_actuelle = aujourd_hui.year
            for annee in range(2026, annee_actuelle + 1):
                abo = Abonnement.objects.filter(
                    est_paye         = True,
                    created_at__year = annee,
                ).aggregate(t=Sum('prix_paye'))['t'] or 0

            ven = Vente.objects.filter(
                created_at__year = annee,
            ).aggregate(t=Sum('prix_total'))['t'] or 0

            revenus_courbe.append({
                'label'  : str(annee),
                'montant': float(abo) + float(ven)
            })
            
           
        # ── Meilleur mois + moyenne + croissance ─
        if revenus_courbe:
            meilleur    = max(revenus_courbe, key=lambda x: x['montant'])
            moyenne     = round(
                sum(r['montant'] for r in revenus_courbe) / len(revenus_courbe), 2
            )
        else:
            meilleur = {'label': '-', 'montant': 0}
            moyenne  = 0

        # ── Types abonnements ────────────────────
        total_abonnements = Abonnement.objects.count()
        types = Abonnement.objects.values('type').annotate(
            count=Count('id')
        ).order_by('-count')

        TYPE_LABELS = {
            'essai'   : 'Essai',
            'normale' : 'Normale',
            'pack10'  : 'Pack 10',
            'pack20'  : 'Pack 20',
        }

        abonnements_par_type = [
            {
                'type'        : t['type'],
                'label'       : TYPE_LABELS.get(t['type'], t['type']),
                'count'       : t['count'],
                'pourcentage' : round(t['count'] / total_abonnements * 100, 1)
                                if total_abonnements > 0 else 0,
            }
            for t in types
        ]

        return Response({
            # Revenus
            'revenu_jour'          : revenu_jour,
            'revenu_mois'          : revenu_mois,
            'revenu_annee'         : revenu_annee,

            # Clients
            'clients_actifs'       : clients_actifs,

            # Séances
            'seances_aujourd_hui'  : seances_aujourd_hui,
            'taux_remplissage'     : taux_remplissage,

            # Expirations
            'expirations_proches'  : expirations_data,
            'expirations_count'    : len(expirations_data),

            # Courbe
            'revenus_courbe'       : revenus_courbe,
            'meilleur_mois'        : meilleur,
            'moyenne_mensuelle'    : moyenne,

            # Types abonnements
            'abonnements_par_type' : abonnements_par_type,

            # Séances du jour tableau
            'seances_du_jour'      : seances_data,
        })