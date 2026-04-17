from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.conf import settings

from .models import PaymentIntent
from .serializers import (
    PaymentIntentSerializer, PaymentCreateSerializer, 
    PaymentConfirmSerializer, PaymentCaptureSerializer
)
from .processors.stripe_adapter import StripeAdapter
from apikeys.permissions import RequiresScope

def get_processor():
    # Factory to get the active payment processor
    # For now, it's always Stripe as per Step 6
    return StripeAdapter

class PaymentIntentViewSet(viewsets.ModelViewSet):
    queryset = PaymentIntent.objects.all()
    serializer_class = PaymentIntentSerializer
    permission_classes = [permissions.IsAuthenticated | RequiresScope]

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            self.required_scope = 'payments:read'
        else:
            self.required_scope = 'payments:write'
        return super().get_permissions()

    @action(detail=False, methods=['post'], url_path='intents')
    def create_intent(self, request):
        """POST /payments/intents — Create a new payment intent."""
        serializer = PaymentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        data = serializer.validated_data
        processor = get_processor()
        
        # 1. Create intent on the processor (Stripe)
        try:
            p_res = processor.create_intent(
                amount=data['amount'],
                currency=data['currency'],
                customer_id=data.get('customer_id'),
                metadata=data.get('metadata'),
                capture_method=data['capture_method']
            )
        except Exception as e:
            return Response({"error": {"code": "processor_error", "message": str(e)}}, status=400)

        # 2. Record in our DB
        intent = PaymentIntent.objects.create(
            amount=data['amount'],
            currency=data['currency'],
            status=p_res['status'],
            processor_id=p_res['processor_id'],
            client_secret=p_res['client_secret'],
            capture_method=data['capture_method'],
            metadata=data.get('metadata', {})
        )
        
        return Response(PaymentIntentSerializer(intent).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        """POST /payments/{id}/confirm — Confirm a payment intent with a method token."""
        intent = self.get_object()
        serializer = PaymentConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        processor = get_processor()
        try:
            p_res = processor.confirm(intent.processor_id, serializer.validated_data['payment_method_id'])
            intent.status = p_res['status']
            intent.save()
        except Exception as e:
            return Response({"error": {"code": "processor_error", "message": str(e)}}, status=400)
            
        return Response(PaymentIntentSerializer(intent).data)

    @action(detail=True, methods=['post'])
    def capture(self, request, pk=None):
        """POST /payments/{id}/capture — Capture funds of an authorized intent."""
        intent = self.get_object()
        serializer = PaymentCaptureSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        processor = get_processor()
        try:
            p_res = processor.capture(intent.processor_id, amount=serializer.validated_data.get('amount'))
            intent.status = p_res['status']
            intent.save()
        except Exception as e:
            return Response({"error": {"code": "processor_error", "message": str(e)}}, status=400)
            
        return Response(PaymentIntentSerializer(intent).data)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """POST /payments/{id}/cancel — Cancel a payment intent."""
        intent = self.get_object()
        
        processor = get_processor()
        try:
            p_res = processor.cancel(intent.processor_id)
            intent.status = p_res['status']
            intent.save()
        except Exception as e:
            return Response({"error": {"code": "processor_error", "message": str(e)}}, status=400)
            
        return Response(PaymentIntentSerializer(intent).data)
