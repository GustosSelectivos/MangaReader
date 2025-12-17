from rest_framework import viewsets, status, filters as drf_filters
from rest_framework.decorators import action
from rest_framework.response import Response
import requests
import os
from rest_framework.permissions import AllowAny
from ApiCore.access_control import DRFDACPermission
from django_filters.rest_framework import DjangoFilterBackend
from ApiCore.Models.chapter_models import chapter
from ApiCore.Serializer.chapter_serializer import ChapterSerializer
from ApiCore.Filter.chapter_filters import ChapterFilter


class ChapterViewSet(viewsets.ModelViewSet):
    queryset = chapter.objects.select_related('manga').all()
    serializer_class = ChapterSerializer
    permission_classes = [DRFDACPermission]
    filter_backends = [DjangoFilterBackend, drf_filters.SearchFilter, drf_filters.OrderingFilter]
    filterset_class = ChapterFilter
    search_fields = ['titulo']
    ordering_fields = ['capitulo_numero', 'id']
    ordering = ['capitulo_numero']

    @action(detail=False, methods=['post'])
    def fetch(self, request):
        try:
            url = request.data.get('url')
            manga_id = request.data.get('manga_id')
            try:
                # Handle '2.00', '2.5', etc.
                val = float(request.data.get('chapter_num', 1))
                chapter_num = int(val) # Truncates decimals for now as worker expects int
            except (ValueError, TypeError):
                chapter_num = 1
            
            series_code = request.data.get('series_code') # Restoring this line
            
            if not url or not manga_id:
                return Response({'error': 'URL and Manga ID are required'}, status=status.HTTP_400_BAD_REQUEST)
                
            # Get Manga Title
            try:
                from ApiCore.Models.manga_models import manga
                m_obj = manga.objects.get(id=manga_id)
                series_title = m_obj.titulo
            except Exception as e:
                # Log this specific error
                print(f"Error fetching manga: {e}")
                return Response({'error': f'Manga not found or error: {e}'}, status=status.HTTP_404_NOT_FOUND)

            # Trigger Worker
            worker_url = os.getenv("WORKER_URL", "http://127.0.0.1:8001")
            worker_api_key = os.getenv("WORKER_API_KEY", "")
            
            payload = {
                "url": url,
                "series_title": series_title,
                "chapter_number": int(chapter_num) if chapter_num else 1,
                "series_code": series_code
            }
            
            headers = {
                "X-API-Key": worker_api_key,
                "Content-Type": "application/json"
            }
            
            # Assuming Worker has /download endpoint
            response = requests.post(f"{worker_url}/download", json=payload, headers=headers, timeout=5)
            if response.status_code == 200:
                return Response({'status': 'Task Started', 'worker_response': response.json()})
            else:
                return Response({'error': 'Worker rejected task', 'details': response.text}, status=status.HTTP_502_BAD_GATEWAY)
        except Exception as e:
             import traceback
             traceback.print_exc()
             return Response({'error': f'Internal Server Error in fetch: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'])
    def completed(self, request):
        """
        Callback from worker when a chapter is fully uploaded.
        Payload: { "series_title": "...", "chapter_number": 1, "status": "success" }
        """
        series_title = request.data.get('series_title')
        chapter_num = request.data.get('chapter_number')
        status_msg = request.data.get('status')
        
        if not series_title or not chapter_num:
            return Response({'error': 'Missing data'}, status=status.HTTP_400_BAD_REQUEST)
            
        print(f"✅ Callback Received: {series_title} #{chapter_num} - {status_msg}")
        
        # Here you would typically update the Chapter status in DB.
        # For now, we log and return success.
        # TODO: Find Chapter and set status='available'
        
        return Response({'status': 'acknowledged'})

    @action(detail=False, methods=['get'])
    def worker_status(self, request):
        """
        Proxy request to get worker status.
        """
        worker_url = os.getenv("WORKER_URL", "http://127.0.0.1:8001")
        worker_api_key = os.getenv("WORKER_API_KEY", "")
        
        try:
            resp = requests.get(f"{worker_url}/status", headers={"X-API-Key": worker_api_key}, timeout=3)
            if resp.status_code == 200:
                return Response(resp.json())
            else:
                return Response({'status': 'offline', 'error': f'Worker returned {resp.status_code}'})
        except Exception:
            return Response({'status': 'offline'})
