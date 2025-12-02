from django.contrib import admin

# Register your models here.

from django.contrib import admin
from .models import Archivo, Cliente, Factura, Pago, Conciliacion

admin.site.register(Archivo)
admin.site.register(Cliente)
admin.site.register(Factura)
admin.site.register(Pago)
admin.site.register(Conciliacion)