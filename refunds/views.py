from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from .models import Refund
from .serializers import RefundSerializer, RefundCreateSerializer
from payments.models import PaymentIntent
from payments.views import get_processor
from apikeys.permissions import RequiresScope

class RefundViewSet(viewsets.ModelViewSet):
    queryset = Refund.objects.all()
    serializer_class = RefundSerializer
    permission_classes = [permissions.IsAuthenticated | RequiresScope]

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            self.required_scope = 'refunds:read'
        else:
            self.required_scope = 'refunds:write'
        return super().get_permissions()

    def create(self, request, *args, **kwargs):
        """POST /refunds — Create a refund."""
        serializer = RefundCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        data = serializer.validated_data
        try:
            payment = PaymentIntent.objects.get(id=data['payment_id'])
        except PaymentIntent.DoesNotExist:
            return Response({"error": "Payment not found"}, status=404)

        processor = get_processor()
        try:
            p_res = processor.create_refund(
                processor_id=payment.processor_id,
                amount=data.get('amount'),
                metadata=data.get('metadata')
            )
            
            refund = Refund.objects.create(
                payment=payment,
                amount=data.get('amount') or payment.amount,
                currency=payment.currency,
                status='succeeded' if p_res['status'] in ['succeeded', 'pending'] else 'failed',
                reason=data.get('reason'),
                processor_id=p_res['processor_id'],
                metadata=data.get('metadata', {})
            )
            
            # Emit event (handled in Step 10)
            # fire_webhook.delay('payment.refunded', RefundSerializer(refund).data)
            
            return Response(RefundSerializer(refund).data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=400)
