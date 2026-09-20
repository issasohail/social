from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render

from .models import Board


@login_required
def board_dashboard(request, code):
	board = get_object_or_404(Board, code=code, is_active=True)
	return render(request, 'boards/dashboard.html', {'board': board, 'cases': board.cases.select_related('person', 'assigned_to')[:50]})
