import os
import django
import sys
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sanofi.settings')
django.setup()

from core.models import Cliente, Factura
from core.services import conciliacion_service

def run_test():
    print("Starting Reconciliation Test...")
    
    # Clean up
    Cliente.objects.all().delete()
    
    # Create Client
    c = Cliente.objects.create(nombre="Test Client", saldo=0)
    print(f"Client created: {c.nombre}, Saldo: {c.saldo}")
    
    # 1. Create COBRO Invoice (100)
    f1 = Factura.objects.create(
        numero_factura="C001",
        cliente=c,
        fecha_emision="2023-01-01",
        monto=100,
        moneda="USD",
        tipo="COBRO"
    )
    print(f"Created COBRO C001: 100. State: {f1.estado}, Saldo Pendiente: {f1.saldo_pendiente}")
    
    c.refresh_from_db()
    print(f"Client Saldo after C001: {c.saldo} (Expected -100)")
    
    # 2. Create PAGO Invoice (50) - Partial Payment
    p1 = Factura.objects.create(
        numero_factura="P001",
        cliente=c,
        fecha_emision="2023-01-02",
        monto=50,
        moneda="USD",
        tipo="PAGO"
    )
    print(f"Created PAGO P001: 50. State: {p1.estado}")
    
    # Reconciliation should have happened automatically on save
    f1.refresh_from_db()
    p1.refresh_from_db()
    c.refresh_from_db()
    
    print(f"After P001 (50):")
    print(f"  C001 State: {f1.estado}, Saldo Pendiente: {f1.saldo_pendiente} (Expected 50)")
    print(f"  P001 State: {p1.estado}, Saldo Pendiente: {p1.saldo_pendiente} (Expected 0 -> CLOSED)")
    print(f"  Client Saldo: {c.saldo} (Expected -50)")
    
    # 3. Create PAGO Invoice (60) - Overpayment for C001
    p2 = Factura.objects.create(
        numero_factura="P002",
        cliente=c,
        fecha_emision="2023-01-03",
        monto=60,
        moneda="USD",
        tipo="PAGO"
    )
    
    f1.refresh_from_db()
    p2.refresh_from_db()
    c.refresh_from_db()
    
    print(f"After P002 (60):")
    print(f"  C001 State: {f1.estado}, Saldo Pendiente: {f1.saldo_pendiente} (Expected 0 -> CLOSED)")
    print(f"  P002 State: {p2.estado}, Saldo Pendiente: {p2.saldo_pendiente} (Expected 10)")
    print(f"  Client Saldo: {c.saldo} (Expected 10)")
    
    # 4. Create COBRO Invoice (10)
    f2 = Factura.objects.create(
        numero_factura="C002",
        cliente=c,
        fecha_emision="2023-01-04",
        monto=10,
        moneda="USD",
        tipo="COBRO"
    )
    
    f2.refresh_from_db()
    p2.refresh_from_db()
    
    print(f"After C002 (10):")
    print(f"  C002 State: {f2.estado}, Saldo Pendiente: {f2.saldo_pendiente} (Expected 0 if auto-reconciled, else 10)")
    print(f"  P002 State: {p2.estado}, Saldo Pendiente: {p2.saldo_pendiente} (Expected 0 if auto-reconciled, else 10)")
    
    if f2.estado == 'OPEN':
        print("  -> Not auto-reconciled on COBRO creation. Triggering manually...")
        conciliacion_service.conciliar_pagos(c.id)
        f2.refresh_from_db()
        p2.refresh_from_db()
        print(f"  C002 State: {f2.estado}, Saldo Pendiente: {f2.saldo_pendiente}")
        print(f"  P002 State: {p2.estado}, Saldo Pendiente: {p2.saldo_pendiente}")

if __name__ == "__main__":
    run_test()
