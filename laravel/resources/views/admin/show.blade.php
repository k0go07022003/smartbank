@extends('layout')
@section('title','Szczegóły użytkownika')
@section('content')
<div class="page-head"><div><span class="eyebrow">PANEL ADMINISTRATORA</span><h1>{{ $user->name }}</h1><p class="muted">Użytkownik #{{ $user->id }}</p></div><a class="button" href="{{ route('users.edit',$user) }}">Edytuj dane</a></div>
<div class="transfer-grid"><section class="panel"><h2>Dane konta</h2><dl><dt>E-mail</dt><dd>{{ $user->email }}</dd><dt>Uprawnienia</dt><dd>{{ $user->role==='admin'?'Administrator':'Klient' }}</dd><dt>Dostęp</dt><dd>{{ $user->is_active?'Odblokowany':'Zablokowany' }}</dd><dt>Aktywacja e-mail</dt><dd>{{ $user->hasVerifiedEmail()?'Potwierdzony':'Niepotwierdzony' }}</dd><dt>Numer rachunku</dt><dd>{{ $user->account->number }}</dd><dt>Saldo</dt><dd>{{ App\Support\Money::format($user->account->balance) }}</dd></dl><a href="{{ route('users.index') }}">← Lista użytkowników</a></section>
@if(auth()->id() !== $user->id)<aside class="panel summary"><h2>Usuń użytkownika</h2><p class="muted">Usunięcie wyłącza dostęp do konta. Historia przelewów zostaje zachowana. Saldo musi wynosić zero.</p><form method="post" action="{{ route('users.destroy',$user) }}">@csrf @method('DELETE')<label class="check"><input type="checkbox" required> Potwierdzam usunięcie użytkownika</label><button class="danger" type="submit">Usuń użytkownika</button></form></aside>@endif</div>
@endsection
