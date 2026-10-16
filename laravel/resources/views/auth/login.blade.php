@extends('layout')
@section('title','Logowanie')
@section('content')
<div class="auth-grid"><section class="intro"><span class="eyebrow">BANKOWOŚĆ W TWOIM RYTMIE</span><h1>Twoje finanse.<br><span>Przejrzyście.</span></h1><p>Saldo, przelewy i historia rachunku.<br>Wszystko w jednym miejscu.</p><div class="mini-card"><span>SmartBank</span><strong>Twój codzienny rachunek</strong><span>Prosto. Wygodnie. Pod kontrolą.</span></div></section>
<section class="panel"><span class="eyebrow">DOBRZE CIĘ WIDZIEĆ</span><h2>Zaloguj się</h2><p class="muted">Uzyskaj dostęp do swojego konta.</p>
<form method="post" action="{{ route('login') }}">@csrf
<label for="email">Adres e-mail</label><input id="email" name="email" type="email" value="{{ old('email') }}" required autocomplete="username" autofocus>
<label for="password">Hasło</label><input id="password" name="password" type="password" required autocomplete="current-password">
<button class="full" type="submit">Zaloguj się <span>→</span></button></form><p class="form-foot">Nie masz konta? <a href="{{ route('register') }}">Zarejestruj się</a></p>
</section></div>
@endsection
