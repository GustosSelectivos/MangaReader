from rest_framework import serializers
from ApiCore.models.mantenedor_models import autores, estados, demografia, tags


class AutorSerializer(serializers.ModelSerializer):
	class Meta:
		model = autores
		fields = ['id', 'nombre', 'tipo_autor', 'foto', 'creado_en', 'vigente']


class EstadoSerializer(serializers.ModelSerializer):
	class Meta:
		model = estados
		fields = ['id', 'descripcion', 'vigente']


class DemografiaSerializer(serializers.ModelSerializer):
	class Meta:
		model = demografia
		fields = ['id', 'descripcion', 'color', 'vigente']
	

class TagSerializer(serializers.ModelSerializer):
	class Meta:
		model = tags
		# Algunos modelos de tags no tienen campo 'color'; limitar a campos válidos
		fields = ['id', 'descripcion', 'vigente']

