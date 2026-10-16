@extends('layout')
@section('title','Użytkownicy')
@section('content')
<div class="page-head"><div><span class="eyebrow">PANEL ADMINISTRATORA</span><h1>Użytkownicy</h1><p class="muted">Zarządzaj kontami i dostępem do aplikacji.</p></div><a class="button" href="{{ route('users.create') }}">+ Dodaj użytkownika</a></div>
<section class="panel"><div class="section-head"><h2>Wszystkie konta</h2><span class="badge">{{ $users->total() }} użytkowników</span></div><div class="table-wrap"><table><thead><tr><th>Użytkownik</th><th>Rola</th><th>Status</th><th>Saldo</th><th>Akcje</th></tr></thead><tbody>@forelse($users as $user)<tr><td><strong>{{ $user->name }}</strong><small>{{ $user->email }}</small></td><td>{{ $user->role==='admin'?'Administrator':'Klient' }}</td><td>{{ !$user->is_active?'Zablokowany':($user->hasVerifiedEmail()?'Aktywny':'Czeka na aktywację') }}</td><td>{{ App\Support\Money::format($user->account->balance) }}</td><td><a href="{{ route('users.show',$user) }}">Szczegóły →</a></td></tr>@empty<tr><td colspan="5">Brak użytkowników.</td></tr>@endforelse</tbody></table></div>{{ $users->links('partials.pagination') }}</section>
@endsection
