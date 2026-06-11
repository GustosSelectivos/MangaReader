
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
        Uploads a cover and returns a normalized URL to the Cloudflare worker
        """
        try:
            key = f'covers/{serie_code}/{filename}'
            
            self.s3.upload_fileobj(
                file_obj,
                self.bucket_name,
                key,
                ExtraArgs={'ContentType': file_obj.content_type}
            )
            
            # WORKER para covers (resize dinámico)
            return f"https://img.miswebtoons.uk/file/MangaApi/{key}"

        except Exception as e:
            print(f"Error uploading cover: {e}")
            return None

    def upload_chapter_page(self, serie_code, chapter_num, file_obj, filename):
        """
        Uploads a chapter page -> devuelve URL del WORKER (blackblaze.miswebtoons.uk)
        """
        try:
            key = f'chapters/{serie_code}/{chapter_num}/{filename}'
            
            self.s3.upload_fileobj(
                file_obj,
                self.bucket_name,
                key,
                ExtraArgs={'ContentType': file_obj.content_type}
            )
            
            # WORKER para chapters (cache + compresión)
            return f"https://blackblaze.miswebtoons.uk/file/MangaApi/{key}"

        except Exception as e:
            print(f"Error uploading chapter: {e}")
            return None

    @staticmethod
    def normalize_image_url(url):
        """
        Converts any Backblaze URL format to worker URL, detecting cover vs chapter
        """
        if not url:
            return None
        
        if 'img.miswebtoons.uk' in url or 'blackblaze.miswebtoons.uk' in url:
            return url
            
        path = None
        if '/file/MangaApi/' in url:
            path = url.split('/file/MangaApi/')[1]
        elif '/MangaApi/' in url:
            path = url.split('/MangaApi/')[1]
            
        if not path:
            return url
            
        # Detecta si es cover o chapter
        if path.startswith('covers/'):
            # COVER -> img.miswebtoons.uk
            return f"https://img.miswebtoons.uk/file/MangaApi/{path}"
        elif path.startswith('chapters/'):
            # CHAPTER -> blackblaze.miswebtoons.uk
            return f"https://blackblaze.miswebtoons.uk/file/MangaApi/{path}"
            
        return url

