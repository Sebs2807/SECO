from core.models import Factura, Conciliacion
from datetime import date

from django.db import transaction

def conciliar_pagos(cliente_id):
    cobros = Factura.objects.filter(cliente_id=cliente_id, tipo='COBRO', estado='OPEN').order_by('fecha_emision')
    pagos = Factura.objects.filter(cliente_id=cliente_id, tipo='PAGO', estado='OPEN').order_by('fecha_emision')

    for pago in pagos:
        monto_disponible = pago.monto

        for cobro in cobros:
            if cobro.estado == 'CLOSED':
                continue

            restante_cobro = cobro.monto - sum(c.monto_aplicado for c in cobro.conciliaciones_cobro.all())

            if monto_disponible >= restante_cobro:
                Conciliacion.objects.create(factura_cobro=cobro, factura_pago=pago, monto_aplicado=restante_cobro, fecha=date.today())
                cobro.estado = 'CLOSED'
                cobro.save()
                monto_disponible -= restante_cobro
            else:
                Conciliacion.objects.create(factura_cobro=cobro, factura_pago=pago, monto_aplicado=monto_disponible, fecha=date.today())
                monto_disponible = 0
                break

        if monto_disponible == 0:
            pago.estado = 'CLOSED'
            pago.save()

