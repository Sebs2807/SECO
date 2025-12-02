from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ClienteViewSet, FacturaViewSet, PagoViewSet, ArchivoViewSet, ConciliacionViewSet
from .views import conciliar_cliente, graficas_page

router = DefaultRouter()
router.register('clientes', ClienteViewSet)
router.register('facturas', FacturaViewSet)
router.register('pagos', PagoViewSet)
router.register('archivos', ArchivoViewSet)
router.register('conciliaciones', ConciliacionViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('conciliar/<str:cliente_id>/', conciliar_cliente),
    path('graficas/', graficas_page),
]
