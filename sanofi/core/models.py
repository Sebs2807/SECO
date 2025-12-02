from django.db import models

class Archivo(models.Model):
    nombre = models.CharField(max_length=50)
    fecha_carga = models.DateField()
    usuario = models.CharField(max_length=50)

    def __str__(self):
        return self.nombre


class Cliente(models.Model):
    nombre = models.CharField(max_length=50)
    nit = models.CharField(max_length=50, blank=True, null=True, unique=True)
    direccion = models.CharField(max_length=50, blank=True, null=True)
    correo = models.CharField(max_length=50, blank=True, null=True)
    telefono = models.CharField(max_length=50, blank=True, null=True)
    pais = models.CharField(max_length=50, blank=True, null=True)
    ciudad = models.CharField(max_length=50, blank=True, null=True)
    archivo = models.ForeignKey(Archivo, on_delete=models.SET_NULL, null=True, related_name='clientes')
    saldo = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def __str__(self):
        return self.nombre


class Factura(models.Model):
    numero_factura = models.CharField(max_length=50, unique=True)  # no como PK
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='facturas')
    fecha_emision = models.DateField()
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    moneda = models.CharField(max_length=25)
    tipo = models.CharField(max_length=10, choices=[('COBRO', 'Cobro'), ('PAGO', 'Pago')])
    estado = models.CharField(max_length=10, choices=[('OPEN', 'Abierto'), ('CLOSED', 'Cerrado')], default='OPEN')
    created_at = models.DateTimeField(auto_now_add=True)
    saldo_pendiente = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def __str__(self):
        return f"Factura {self.numero_factura}"

    def _delta_for(self):
        """Return the signed delta that this factura contributes to cliente.saldo.

        Convention: COBRO decreases balance (negative), PAGO increases it (positive).
        """
        from decimal import Decimal
        amt = Decimal(self.monto or 0)
        if self.tipo == 'PAGO':
            return amt
        # COBRO
        return -amt

    def save(self, *args, **kwargs):
        """Override save to update cliente.saldo automatically and atomically.

        Uses a DB transaction and F expressions to ensure updates are applied
        atomically and avoid race conditions. If something goes wrong you can
        also call `recompute_saldos()` to rebuild balances from stored facturas.
        """
        from decimal import Decimal
        from django.db import transaction
        from django.db.models import F, Value
        
        # Import service here to avoid circular imports
        try:
            from .services import conciliacion_service
        except ImportError:
            conciliacion_service = None

        old = None
        if self.pk:
            try:
                old = Factura.objects.get(pk=self.pk)
            except Factura.DoesNotExist:
                old = None
        
        # Initialize saldo_pendiente for new invoices
        if not self.pk:
            self.saldo_pendiente = self.monto

        # Save the factura first (validations, unique constraints, etc.)
        super().save(*args, **kwargs)

        new_delta = self._delta_for()

        # Apply deltas inside a transaction using DB-side updates (F expressions)
        with transaction.atomic():
            if old is None:
                # New factura: add new_delta to this cliente
                Cliente.objects.filter(pk=self.cliente_id).update(saldo=F('saldo') + Value(new_delta))
            else:
                old_delta = old._delta_for()

                if old.cliente_id == self.cliente_id:
                    # Same client: apply the difference
                    diff = new_delta - old_delta
                    if diff != Decimal('0'):
                        Cliente.objects.filter(pk=self.cliente_id).update(saldo=F('saldo') + Value(diff))
                else:
                    # Different clients: revert old_delta from old client and add new_delta to new client
                    Cliente.objects.filter(pk=old.cliente_id).update(saldo=F('saldo') - Value(old_delta))
                    Cliente.objects.filter(pk=self.cliente_id).update(saldo=F('saldo') + Value(new_delta))
        
        # Trigger reconciliation if it's a PAGO
        if self.tipo == 'PAGO' and conciliacion_service:
            conciliacion_service.conciliar_pagos(self.cliente_id)

    def delete(self, *args, **kwargs):
        """When deleting a factura, revert its applied delta from the cliente.saldo.

        Uses a transaction and DB-level update to ensure atomicity.
        """
        from django.db import transaction
        from django.db.models import F, Value

        delta = self._delta_for()
        cliente_id = self.cliente_id

        with transaction.atomic():
            super().delete(*args, **kwargs)
            # Subtract the delta from the cliente saldo
            Cliente.objects.filter(pk=cliente_id).update(saldo=F('saldo') - Value(delta))


def recompute_saldos():
    """Recompute and set all clientes.saldo from scratch based on stored facturas.

    This is useful as a corrective/maintenance operation if balances get
    out-of-sync for any reason. It performs DB-level updates in a transaction.
    """
    from django.db import transaction
    from django.db.models import Sum, Case, When, Value, DecimalField

    with transaction.atomic():
        # Compute per-client sum: PAGO => +monto, COBRO => -monto
        from django.db.models import F

        agg = Factura.objects.values('cliente').annotate(
            saldo_sum=Sum(
                Case(
                    When(tipo='PAGO', then=F('monto')),
                    When(tipo='COBRO', then=Value(0) - F('monto')),
                    output_field=DecimalField(max_digits=12, decimal_places=2),
                )
            )
        )

        # Reset all clientes to zero first
        Cliente.objects.all().update(saldo=Value(0))

        # Apply computed sums
        for row in agg:
            cliente_id = row['cliente']
            saldo = row['saldo_sum'] or 0
            Cliente.objects.filter(pk=cliente_id).update(saldo=saldo)


class Pago(models.Model):
    numero_factura = models.ForeignKey(Factura, on_delete=models.CASCADE, related_name='pagos')
    fecha = models.DateField()
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    metodo = models.CharField(max_length=50)
    comprobante_url = models.CharField(max_length=500, blank=True, null=True)

    def __str__(self):
        return f"Pago {self.id}"


class Conciliacion(models.Model):
    fecha = models.DateField(auto_now_add=True)
    monto_aplicado = models.DecimalField(max_digits=12, decimal_places=2)
    usuario = models.CharField(max_length=50)
    factura_pago = models.ForeignKey(Factura, on_delete=models.CASCADE, related_name='conciliaciones_pago')
    factura_cobro = models.ForeignKey(Factura, on_delete=models.CASCADE, related_name='conciliaciones_cobro')

    def __str__(self):
        return f"Conciliación {self.id}"
