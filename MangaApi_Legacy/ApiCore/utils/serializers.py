from rest_framework import serializers

class DynamicFieldsModelSerializer(serializers.ModelSerializer):
    """
    A ModelSerializer that takes an additional `fields` argument that
    controls which fields should be displayed.
    Usage: /api/endpoint/?fields=id,name
    """
    def __init__(self, *args, **kwargs):
        # Don't pass the 'fields' arg up to the superclass
        fields = kwargs.pop('fields', None)

        super().__init__(*args, **kwargs)

        if fields is not None:
             allowed = set(fields)
             existing = set(self.fields)
             for field_name in existing - allowed:
                 self.fields.pop(field_name)
        
        # Also check context for request query params
        request = self.context.get('request')
        if request:
            params = request.query_params.get('fields')
            if params:
                allowed = set(params.split(','))
                existing = set(self.fields)
                for field_name in existing - allowed:
                    self.fields.pop(field_name)
