from django.db import transaction
from .models import Factura, Cliente, Conciliacion
from decimal import Decimal

class ConciliacionService:
    def conciliar_pagos(self, cliente_id):
        """
        Reconcile payments for a client.
        Matches OPEN PAGO invoices against OPEN COBRO invoices.
        """
        with transaction.atomic():
            # Lock the client to prevent concurrent reconciliations
            cliente = Cliente.objects.select_for_update().get(pk=cliente_id)
            
            # Get all OPEN PAGOs (oldest first)
            pagos = list(Factura.objects.filter(
                cliente=cliente, 
                tipo='PAGO', 
                estado='OPEN'
            ).order_by('created_at').select_for_update())
            
            # Get all OPEN COBROs (oldest first)
            cobros = list(Factura.objects.filter(
                cliente=cliente, 
                tipo='COBRO', 
                estado='OPEN'
            ).order_by('created_at').select_for_update())
            
            if not pagos or not cobros:
                return

            pago_idx = 0
            cobro_idx = 0
            
            while pago_idx < len(pagos) and cobro_idx < len(cobros):
                pago = pagos[pago_idx]
                cobro = cobros[cobro_idx]
                
                # Available amount in this payment
                available = pago.saldo_pendiente
                # Amount needed for this charge
                needed = cobro.saldo_pendiente
                
                if available <= 0:
                    # Should not happen if filtered by OPEN and logic is correct, but safety check
                    pago.estado = 'CLOSED'
                    Factura.objects.filter(pk=pago.pk).update(estado='CLOSED')
                    pago_idx += 1
                    continue
                
                if needed <= 0:
                    cobro.estado = 'CLOSED'
                    Factura.objects.filter(pk=cobro.pk).update(estado='CLOSED')
                    cobro_idx += 1
                    continue

                # Determine how much we can apply
                applied = min(available, needed)
                
                # Create Conciliacion record
                Conciliacion.objects.create(
                    monto_aplicado=applied,
                    usuario='system', # Or pass user if available
                    factura_pago=pago,
                    factura_cobro=cobro
                )
                
                # Update balances
                pago.saldo_pendiente -= applied
                cobro.saldo_pendiente -= applied
                
                # Check if fully used/paid
                if pago.saldo_pendiente == 0:
                    pago.estado = 'CLOSED'
                    pago_idx += 1
                
                if cobro.saldo_pendiente == 0:
                    cobro.estado = 'CLOSED'
                    cobro_idx += 1
                
                # Use update() to avoid recursion (save() triggers reconciliation)
                Factura.objects.filter(pk=pago.pk).update(
                    saldo_pendiente=pago.saldo_pendiente,
                    estado=pago.estado
                )
                Factura.objects.filter(pk=cobro.pk).update(
                    saldo_pendiente=cobro.saldo_pendiente,
                    estado=cobro.estado
                )

conciliacion_service = ConciliacionService()
