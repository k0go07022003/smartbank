@extends('layout')
@section('title','Rejestracja')
@section('content')
<div class="narrow panel"><span class="eyebrow">ZACZNIJ OD SWOJEGO KONTA</span><h1>Dołącz do SmartBank</h1><p class="muted">Po rejestracji potwierdź swój adres e-mail.</p>
<form method="post" action="{{ route('register') }}">@csrf
@include('partials.identity',['user'=>null])
<button class="full" type="submit">Utwórz konto →</button></form><p class="form-foot">Masz już konto? <a href="{{ route('login') }}">Zaloguj się</a></p></div>
@endsection
