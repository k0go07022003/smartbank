@if($transfers->isEmpty())<div class="empty"><span class="empty-icon">↗</span><h3>Tu zaczyna się Twoja historia</h3><p class="muted">Wykonane i otrzymane przelewy pojawią się w tym miejscu.</p><a href="{{ route('transfer.create') }}">Wykonaj pierwszy przelew →</a></div>
@else<div class="table-wrap"><table><thead><tr><th>Odbiorca / nadawca</th><th>Tytuł</th><th>Data</th><th class="amount">Kwota</th></tr></thead><tbody>
@foreach($transfers as $transfer)
@php($outgoing=$transfer->sender_id === $account->id)
@php($other=$outgoing ? $transfer->recipient : $transfer->sender)
<tr><td><strong>{{ $other->user->name }}</strong><small>{{ $other->number }} · {{ $outgoing?'Wychodzący':'Przychodzący' }}</small></td><td>{{ $transfer->title }}</td><td>{{ $transfer->created_at->format('d.m.Y H:i') }}</td><td class="amount {{ $outgoing?'':'positive' }}">{{ $outgoing?'−':'+' }}{{ App\Support\Money::format($transfer->amount) }}</td></tr>
@endforeach
</tbody></table></div>@endif
