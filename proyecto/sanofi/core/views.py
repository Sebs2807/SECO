from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
import importlib

# Try to import the conciliacion_service using the package-aware importlib with fallbacks.
conciliacion_service = None
try:
    # Prefer a relative import when __package__ is set (e.g., running in a package context)
    if __package__:
        try:
            mod = importlib.import_module(f"{__package__}.services")
            conciliacion_service = getattr(mod, 'conciliacion_service', None)
        except Exception:
            # Fallback to common absolute module paths
            mod = importlib.import_module('core.services')
            conciliacion_service = getattr(mod, 'conciliacion_service', None)
    else:
        # If __package__ is empty (script-style execution), try absolute imports
        mod = importlib.import_module('core.services')
        conciliacion_service = getattr(mod, 'conciliacion_service', None)
except Exception:
    conciliacion_service = None
from rest_framework.decorators import action

# Create your views here.

from rest_framework import viewsets
from rest_framework.permissions import AllowAny
from rest_framework.parsers import JSONParser, FormParser, MultiPartParser
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.shortcuts import redirect
from django.urls import reverse
from .models import Cliente, Factura, Pago, Archivo, Conciliacion
from .serializers import ClienteSerializer, FacturaSerializer, PagoSerializer, ArchivoSerializer, ConciliacionSerializer

class ClienteViewSet(viewsets.ModelViewSet):
    queryset = Cliente.objects.all()
    serializer_class = ClienteSerializer
    permission_classes = [AllowAny]
    authentication_classes = []
    # Accept JSON (fetch), form-urlencoded (HTML form), and multipart
    parser_classes = [JSONParser, FormParser, MultiPartParser]

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        request = args[0] if args else None
        try:
            print(f"[ClienteViewSet.dispatch] {request.method} {request.path}")
        except Exception:
            pass
        return super().dispatch(*args, **kwargs)

    def create(self, request, *args, **kwargs):
        # Trace payload
        payload = None
        try:
            payload = request.data
        except Exception:
            pass
        print("[ClienteViewSet.create] Incoming payload:", payload)

        # Perform standard DRF create
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)

        # If request came from an HTML form, redirect back to index
        content_type = (request.content_type or '').lower()
        accept = (request.META.get('HTTP_ACCEPT', '') or '').lower()
        if 'application/x-www-form-urlencoded' in content_type or 'text/html' in accept:
            # optional: flash message via querystring
            try:
                url = reverse('index')
            except Exception:
                url = '/'
            return redirect(url)

        # Otherwise, return JSON
        from rest_framework import status
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

class FacturaViewSet(viewsets.ModelViewSet):
    queryset = Factura.objects.all()
    serializer_class = FacturaSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        cliente_id = self.request.query_params.get('cliente') if hasattr(self, 'request') else None
        if cliente_id:
            try:
                qs = qs.filter(cliente_id=int(cliente_id))
            except (TypeError, ValueError):
                pass
        return qs

    @action(detail=False, methods=['get'])
    def open(self, request):
        facturas = self.get_queryset().filter(estado='OPEN')
        serializer = self.get_serializer(facturas, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def closed(self, request):
        facturas = self.get_queryset().filter(estado='CLOSED')
        serializer = self.get_serializer(facturas, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def aging_buckets(self, request):
        """Return counts of OPEN invoices per client grouped by aging buckets.

        Query params (seconds):
        - b1_start, b1_end (defaults 0-60)
        - b2_start, b2_end (defaults 60-120)
        - b3_start, b3_end (defaults 120-180)

        Buckets are labeled: en_tiempo (b1), pendiente (b2), en_riesgo (b3).
        """
        from datetime import datetime, timezone

        def get_int(name, default):
            try:
                return int(request.query_params.get(name, default))
            except (TypeError, ValueError):
                return default

        b1_start = get_int('b1_start', 0)
        b1_end = get_int('b1_end', 60)
        b2_start = get_int('b2_start', 60)
        b2_end = get_int('b2_end', 120)
        b3_start = get_int('b3_start', 120)
        b3_end = get_int('b3_end', 180)

        now = datetime.now(timezone.utc)

        # Gather OPEN invoices joined with client
        facturas = (
            Factura.objects.select_related('cliente')
            .filter(estado='OPEN')
            .only('id', 'created_at', 'cliente__id', 'cliente__nombre')
        )

        # Build per-client counters
        result = {}
        for f in facturas:
            cliente = f.cliente
            cid = cliente.id
            if cid not in result:
                result[cid] = {
                    'cliente_id': cid,
                    'cliente_nombre': cliente.nombre,
                    'en_tiempo': 0,
                    'pendiente': 0,
                    'en_riesgo': 0,
                }

            # Compute age in minutes
            age_minutes = (now - f.created_at).total_seconds() / 60.0

            if b1_start <= age_minutes <= b1_end:
                result[cid]['en_tiempo'] += 1
            elif b2_start <= age_minutes <= b2_end:
                result[cid]['pendiente'] += 1
            elif b3_start <= age_minutes <= b3_end:
                result[cid]['en_riesgo'] += 1
            # else: outside defined buckets, ignore

        return Response(list(result.values()))

class PagoViewSet(viewsets.ModelViewSet):
    queryset = Pago.objects.all()
    serializer_class = PagoSerializer

class ArchivoViewSet(viewsets.ModelViewSet):
    queryset = Archivo.objects.all()
    serializer_class = ArchivoSerializer

class ConciliacionViewSet(viewsets.ModelViewSet):
    queryset = Conciliacion.objects.all()
    serializer_class = ConciliacionSerializer

@api_view(['POST'])
def conciliar_cliente(request, cliente_id):
    if conciliacion_service and hasattr(conciliacion_service, 'conciliar_pagos'):
        conciliacion_service.conciliar_pagos(cliente_id)
        return Response({"message": f"Conciliación ejecutada para cliente {cliente_id}"})
    return Response({"message": "Servicio de conciliación no disponible"}, status=503)


def index(request):
    """Render a minimal frontend page that interacts with the existing API endpoints."""
    return render(request, 'core/index.html')


def facturas_page(request):
    """Render the facturas management page."""
    return render(request, 'core/facturas.html')


def graficas_page(request):
    """Render the gráficas page for aging buckets visualization."""
    return render(request, 'core/graficas.html')