
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from ApiCore.services.b2_service import B2Service

class B2UploadSignView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Returns a presigned URL for uploading a file to B2.
        Payload: { "file_path": "chapters/code/1.webp", "content_type": "image/webp" }
        """
        file_path = request.data.get('file_path')
        content_type = request.data.get('content_type', 'image/webp')

        if not file_path:
            return Response({'error': 'file_path is required'}, status=400)

        service = B2Service()
        url = service.get_presigned_url(file_path, content_type)

        if url:
            return Response({'url': url})
        else:
            return Response({'error': 'Could not generate URL'}, status=500)
