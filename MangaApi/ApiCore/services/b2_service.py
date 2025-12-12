
import boto3
import os
from botocore.config import Config
from django.conf import settings

class B2Service:
    def __init__(self):
        self.endpoint = os.getenv('B2_ENDPOINT_URL', 'https://s3.us-east-005.backblazeb2.com')
        self.key_id = os.getenv('B2_KEY_ID')
        self.app_key = os.getenv('B2_APPLICATION_KEY')
        self.bucket_name = os.getenv('B2_BUCKET_NAME', 'MangaApi')
        
        self.s3 = boto3.client(
            's3',
            endpoint_url=self.endpoint,
            aws_access_key_id=self.key_id,
            aws_secret_access_key=self.app_key,
            config=Config(signature_version='s3v4')
        )

    def get_presigned_url(self, file_path, content_type='image/webp'):
        """
        Generates a presigned URL for PUT requests (uploading)
        file_path: Relative path in bucket (e.g. 'chapters/code/001/001.webp')
        """
        try:
            url = self.s3.generate_presigned_url(
                ClientMethod='put_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': file_path,
                    'ContentType': content_type
                },
                ExpiresIn=3600  # 1 hour
            )
            return url
        except Exception as e:
            print(f"Error generating presigned URL: {e}")
            return None

    def initialize_manga_folders(self, serie_code):
        """
        Creates empty 'folders' in B2 by uploading a .keep file
        """
        try:
            # Create chapters folder
            self.s3.put_object(
                Bucket=self.bucket_name,
                Key=f'chapters/{serie_code}/.keep',
                Body=b''
            )
            # Create cover folder
            self.s3.put_object(
                Bucket=self.bucket_name,
                Key=f'covers/{serie_code}/.keep',
                Body=b''
            )
            return True
        except Exception as e:
            print(f"Error creating folders: {e}")
            return False

    def upload_cover(self, serie_code, file_obj, filename):
        """
        Uploads a file object to covers/{serie_code}/{filename}
        """
        try:
            key = f'covers/{serie_code}/{filename}'
            # file_obj is a Django UploadedFile, so we can read it
            self.s3.upload_fileobj(
                file_obj,
                self.bucket_name,
                key,
                ExtraArgs={'ContentType': file_obj.content_type}
            )
            # Return public URL (assuming it's public or we construct it)
            # Standard B2 s3 endpoint URL structure:
            # https://{bucketName}.s3.{region}.backblazeb2.com/{key}
            # Or if custom domain is used. For now let's try to construct a reliable URL.
            # Using the endpoint from init might be generic (s3.us-east-005...), verify if we need exact file URL.
            # Usually: https://f005.backblazeb2.com/file/{bucketName}/{key}
            # But let's check what we have.
            # Safe bet: return the Key, and let frontend/serializer handle full URL or use a standard base.
            # However, existing code seems to store full URL or relative?
            # looking at serializer get_url_absoluta, it handles strings starting with http.
            # Let's try to return a full URL if possible.
            
            # Helper to construct typical friendly URL if possible
            friendly_host = self.endpoint.replace('s3.', '').replace('.backblazeb2.com', '.backblazeb2.com/file/' + self.bucket_name)
            # Actuall B2 friendly URL is slightly different usually. 
            # e.g. https://f005.backblazeb2.com/file/MangaApi/cover/...
            # Let's just return the relative B2 key for now if we don't have a sure domain, 
            # OR better: construct the s3 URL which is reliable.
            
            # Actually, let's just use the key. The serializer expects 'url_imagen' char field.
            # If we look at existing data: "https://f005.backblazeb2.com/file/MangaApi/..."
            
            # Let's assume a standard public URL format for B2
            # We can grab it from env or hardcode the prefix if we know it.
            # For now, let's try to deduce it or just return the S3 URI.
            
            # Let's assume standard friendly URL logic:
            public_base = os.getenv('B2_PUBLIC_URL', '').rstrip('/')
            if not public_base:
                # Fallback to direct file download from generic s3 endpoint if nothing else (might not work for web display)
                # But typically B2 gives you a specific naming like f005.
                # Let's try to return the full key path and let the view/serializer assume a prefix if needed?
                # No, we want to save a working URL.
                return f"{self.endpoint}/{self.bucket_name}/{key}" 
            
            return f"{public_base}/{key}"

        except Exception as e:
            print(f"Error uploading cover: {e}")
            return None
