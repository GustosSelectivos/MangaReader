
from django.core.management.base import BaseCommand
from ApiCore.services.b2_service import B2Service

class Command(BaseCommand):
    help = 'Configure CORS for B2 bucket'

    def handle(self, *args, **options):
        service = B2Service()
        bucket_name = service.bucket_name
        
        self.stdout.write(f"Configuring CORS for bucket: {bucket_name}...")
        
        try:
            cors_configuration = {
                'CORSRules': [{
                    'AllowedHeaders': ['*'],
                    'AllowedMethods': ['GET', 'PUT', 'POST', 'HEAD'],
                    'AllowedOrigins': ['*'],  # Or specific domains like http://localhost:5173
                    'ExposeHeaders': ['ETag'],
                    'MaxAgeSeconds': 3600
                }]
            }
            
            service.s3.put_bucket_cors(
                Bucket=bucket_name,
                CORSConfiguration=cors_configuration
            )
            self.stdout.write(self.style.SUCCESS('Successfully configured CORS rules.'))
            
            # Verify
            current = service.s3.get_bucket_cors(Bucket=bucket_name)
            self.stdout.write(f"Current Rules: {current['CORSRules']}")
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error configuring CORS: {e}"))
