from rest_framework import serializers
from .models import Cliente, Factura, Pago, Archivo, Conciliacion

class ClienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cliente
        fields = '__all__'

class FacturaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Factura
        fields = '__all__'

class PagoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pago
        fields = '__all__'

class ArchivoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Archivo
        fields = '__all__'

class ConciliacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Conciliacion
        fields = '__all__'
